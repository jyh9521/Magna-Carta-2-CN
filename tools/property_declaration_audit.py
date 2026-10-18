"""Nested declaration identities, never native offsets or container values."""
from __future__ import annotations
try:
    from .ue3_struct_defaults import property_declaration,parse_struct_defaults
    from .ue3_package import FormatError
except ImportError:
    from ue3_struct_defaults import property_declaration,parse_struct_defaults
    from ue3_package import FormatError


def property_tree(graph,node,bind_structs=False):
    budget=[0]
    def walk(current,stack):
        if current in stack or len(stack)>=16 or budget[0]>=1024:
            raise FormatError('cyclic/overlong/oversize container declaration tree')
        budget[0]+=1;d=property_declaration(graph,current);children=[];container=d.get('container')
        complete=True
        if container:
            if container['kind']=='array':refs=[container['inner']]
            elif container['type_visibility']=='opaque-null-type-references':refs=[];complete=False
            else:refs=[container['key'],container['value']]
            for ref in refs:
                child=walk((current[0],ref['reference']),stack+(current,));children.append(child)
                complete=complete and child['serialized_type_tree_complete']
        result=dict(declaration=d,children=children,serialized_type_tree_complete=complete,
            native_layout_verified=False,container_values_decoded=False)
        if bind_structs and d['kind']=='StructProperty':
            target=graph.reference(current[0],d['target']['reference'])
            result['struct_definition']=parse_struct_defaults(graph,target)
        return result
    return walk(node,())


def class_properties(graph,node,bind_structs=False):
    if graph.export(*node)['class_path']!='Class':raise FormatError('declaration inventory requires exact Class')
    package,index=node;nodes=[(package,i) for i,e in enumerate(graph.packages[package]['tables']['exports'],1)
                             if e['outer']==index and e['class_path'].endswith('Property')]
    if not 1<=len(nodes)<=4096:raise FormatError('local Class property count outside bound')
    trees=[property_tree(graph,n,bind_structs) for n in nodes];by_id={n[1]:t for n,t in zip(nodes,trees)}
    incoming={i:0 for i in by_id}
    for tree in trees:
        ref=tree['declaration']['next_reference']
        if ref:
            if ref<0 or graph.export(package,ref)['outer']!=index:
                raise FormatError('Class property Next reference crosses owner')
            if ref in incoming:
                incoming[ref]+=1
                if incoming[ref]>1:raise FormatError('ambiguous Class property Next predecessor')
    runs=[];seen=set()
    for first in sorted(i for i,count in incoming.items() if not count):
        path=[];current=first
        while current in by_id:
            if current in seen:raise FormatError('cyclic Class property Next run')
            seen.add(current);path.append(graph.describe((package,current)));current=by_id[current]['declaration']['next_reference']
        runs.append(dict(properties=path,boundary=graph.describe((package,current)) if current else None))
    if seen!=set(by_id):raise FormatError('cyclic/uncovered Class property Next declarations')
    return dict(owner=graph.describe(node),properties=trees,local_property_count=len(nodes),
        local_next_runs=runs,inventory_scope='all immediate property exports in supplied object tables',
        class_children_header_decoded=False,inheritance_merged=False,native_layout_verified=False,
        serialized_type_trees_complete=all(t['serialized_type_tree_complete'] for t in trees),container_values_decoded=False)
