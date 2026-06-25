from python_alfresco_api import ClientFactory

factory = ClientFactory(
    base_url="http://localhost:8080/alfresco",
    username="admin",
    password="admin"
)

core = factory.create_core_client()

nodes = core.nodes.list_children(node_id="-root-")

print("✅ Connected successfully to Alfresco!\n")

for entry in nodes.list.entries:
    node = entry.entry
    print(f"- {node.name} (file={node.is_file})")
