# visualize_relations.py
from pyvis.network import Network

# 创建图谱
net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
net.barnes_hut()  # 优化布局

# 添加节点（人物）
all_chars = set()
for (c1, c2), _ in top_relations:
    all_chars.update([c1, c2])

for char in all_chars:
    net.add_node(char, label=char, size=25, title=f"{char}出场次数待统计")

# 添加边（关系）
for (char1, char2), weight in top_relations:
    net.add_edge(char1, char2, value=weight, title=f"共现{weight}次")

net.show("character_relations.html")  # 生成交互式HTML