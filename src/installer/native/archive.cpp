// MIT. Thin streaming adapter over pinned Exzap/ZArchive (MIT-0), not a new
// archive format. Source extents permit packing a validated virtual XEX tree.
#include <zarchive/zarchivewriter.h>
#include <zarchive/zarchivereader.h>
#include "sha_256.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using Bytes = std::vector<uint8_t>;
static constexpr size_t block_size = 1024 * 1024;
static void require(bool ok, const char* message) { if (!ok) throw std::runtime_error(message); }
static std::string lower(std::string s) { for (auto& c : s) if (c >= 'A' && c <= 'Z') c += 32; return s; }
static void safe_name(const std::string& s) {
  require(!s.empty() && s.size() <= 240 && s.front() != '/' && s.back() != '/', "bad archive path");
  std::istringstream in(s); std::string part;
  while (std::getline(in, part, '/')) {
    require(!part.empty() && part != "." && part != ".." && part.back() != ' ' && part.back() != '.', "bad path component");
    for (unsigned char c : part) require(c >= 32 && c <= 126 && std::string("\\:*?\"<>|").find(c) == std::string::npos, "bad path character");
  }
}
static uint64_t number(const std::string& s) {
  require(!s.empty() && s.find_first_not_of("0123456789") == std::string::npos, "bad extent number");
  return std::stoull(s);
}
static std::string hex(const uint8_t* hash) {
  const char* digits = "0123456789abcdef"; std::string result;
  for (int i=0; i<32; ++i) { result += digits[hash[i]>>4]; result += digits[hash[i]&15]; }
  return result;
}
struct Source { std::string name; fs::path path; uint64_t offset, size; };
struct Output { std::ofstream file; };
static void new_file(int32_t part, void*) { require(part == -1, "multipart archive not supported"); }
static void write_data(const void* bytes, size_t size, void* ctx) {
  auto& file = static_cast<Output*>(ctx)->file;
  file.write(static_cast<const char*>(bytes), static_cast<std::streamsize>(size));
  require(file.good(), "archive write failed (disk full or permission error)");
}
static void create(const fs::path& manifest, const fs::path& output) {
  require(!fs::exists(output), "archive output already exists");
  std::ifstream in(manifest); require(in.good(), "cannot open extent manifest");
  std::vector<Source> sources; std::set<std::string> seen; std::string line;
  while (std::getline(in, line)) {
    if (!line.empty() && line.back() == '\r') line.pop_back();
    std::istringstream row(line); std::array<std::string,4> fields;
    for (auto& f : fields) require(bool(std::getline(row, f, '\t')), "malformed extent row");
    require(row.eof(), "extra extent fields"); safe_name(fields[0]);
    require(seen.insert(lower(fields[0])).second, "duplicate archive member");
    Source s{fields[0], fs::u8path(fields[1]), number(fields[2]), number(fields[3])};
    auto length = fs::file_size(s.path);
    require(s.offset <= length && s.size <= length - s.offset, "source extent outside file");
    sources.push_back(s); require(sources.size() <= 20000, "too many files");
  }
  require(!sources.empty(), "empty source manifest");
  Output out{std::ofstream(output, std::ios::binary)}; require(out.file.good(), "cannot create archive");
  ZArchiveWriter writer(new_file, write_data, &out); Bytes buffer(block_size);
  for (size_t i=0; i<sources.size(); ++i) {
    auto& s = sources[i]; auto slash=s.name.find_last_of('/');
    if (slash != std::string::npos) require(writer.MakeDir(s.name.substr(0,slash).c_str(),true), "cannot create archive directory");
    require(writer.StartNewFile(s.name.c_str()), "cannot start archive member");
    std::ifstream file(s.path,std::ios::binary); require(file.good(),"cannot read source"); file.seekg(s.offset);
    uint64_t remain=s.size;
    while (remain) {
      auto count=static_cast<size_t>(std::min<uint64_t>(remain,buffer.size()));
      file.read(reinterpret_cast<char*>(buffer.data()), count); require(size_t(file.gcount())==count,"short source read");
      writer.AppendData(buffer.data(), count); remain-=count;
    }
    std::cout << "PROGRESS " << double(i+1)/sources.size() << ' ' << s.name << std::endl;
  }
  writer.Finalize(); out.file.flush(); require(out.file.good(), "archive flush failed");
  std::cout << "CREATED " << sources.size() << std::endl;
}
static void verify_integrity(const fs::path& archive) {
  // Upstream WriteFooter hashes every byte with the footer's integrityHash zeroed.
  const uint64_t size=fs::file_size(archive); const size_t footer_size=sizeof(_ZARCHIVE::Footer);
  require(size>=footer_size,"truncated archive footer");
  std::ifstream file(archive,std::ios::binary); file.seekg(size-footer_size);
  Bytes footer(footer_size); file.read(reinterpret_cast<char*>(footer.data()),footer_size);
  const auto at=offsetof(_ZARCHIVE::Footer,integrityHash);
  std::array<uint8_t,32> expected{}; std::copy_n(footer.data()+at,32,expected.data());
  std::fill_n(footer.data()+at,32,0); file.clear(); file.seekg(0);
  Sha_256 sha; uint8_t result[32]; sha_256_init(&sha,result); Bytes buffer(block_size); auto remaining=size-footer_size;
  while(remaining) {
    auto count=static_cast<size_t>(std::min<uint64_t>(remaining,buffer.size()));
    file.read(reinterpret_cast<char*>(buffer.data()),count); require(size_t(file.gcount())==count,"short archive read");
    sha_256_write(&sha,buffer.data(),count); remaining-=count;
  }
  sha_256_write(&sha,footer.data(),footer.size()); sha_256_close(&sha);
  require(std::equal(expected.begin(),expected.end(),result),"ZArchive footer SHA256 mismatch");
}
static void verify(const fs::path& archive, const fs::path& report) {
  require(!fs::exists(report),"verification output already exists"); verify_integrity(archive);
  std::unique_ptr<ZArchiveReader> reader(ZArchiveReader::OpenFromFile(archive)); require(bool(reader),"ZArchive read failed");
  std::vector<std::string> pending{""}, files; std::set<std::string> seen;
  while(!pending.empty()) {
    auto parent=pending.back(); pending.pop_back(); auto handle=reader->LookUp(parent,false,true);
    require(reader->IsDirectory(handle),"invalid archive directory");
    auto count=reader->GetDirEntryCount(handle); require(count<=20000,"directory count exceeds bound");
    for(uint32_t i=0;i<count;++i) {
      ZArchiveReader::DirEntry entry; require(reader->GetDirEntry(handle,i,entry),"invalid archive entry");
      auto name=parent.empty()?std::string(entry.name):parent+"/"+std::string(entry.name); safe_name(name);
      require(seen.insert(lower(name)).second && seen.size()<=40000,"duplicate/cyclic archive tree");
      if(entry.isFile) files.push_back(name); else { require(entry.isDirectory,"unknown archive node"); pending.push_back(name); }
    }
  }
  std::sort(files.begin(),files.end()); std::ofstream output(report,std::ios::binary); require(output.good(),"cannot write report"); Bytes buffer(block_size);
  for(size_t i=0;i<files.size();++i) {
    auto handle=reader->LookUp(files[i]); auto size=reader->GetFileSize(handle); Sha_256 sha; uint8_t result[32]; sha_256_init(&sha,result);
    for(uint64_t at=0;at<size;) {
      auto count=std::min<uint64_t>(size-at,buffer.size()); require(reader->ReadFromFile(handle,at,count,buffer.data())==count,"archive member read failed");
      sha_256_write(&sha,buffer.data(),size_t(count)); at+=count;
    }
    sha_256_close(&sha); output<<hex(result)<<'\t'<<size<<'\t'<<files[i]<<'\n';
    std::cout<<"PROGRESS "<<double(i+1)/files.size()<<' '<<files[i]<<std::endl;
  }
  output.flush(); require(output.good(),"report write failed"); std::cout<<"VERIFIED "<<files.size()<<std::endl;
}
#ifdef _WIN32
int wmain(int argc, wchar_t** argv) {
#else
int main(int argc, char** argv) {
#endif
  try {
    require(argc==4,"Usage: mc2-zar create sources.tsv output.zar | verify input.zar report.tsv");
    auto mode=fs::path(argv[1]).string();
    if(mode=="create") create(argv[2],argv[3]); else if(mode=="verify") verify(argv[2],argv[3]); else throw std::runtime_error("unknown operation");
    return 0;
  } catch(const std::exception& error) { std::cerr<<"ERROR "<<error.what()<<std::endl; return 2; }
}
