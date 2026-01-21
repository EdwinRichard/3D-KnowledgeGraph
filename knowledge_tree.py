import json
import uuid
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class KnowledgeNode:
    """全景节点"""
    id: str
    name: str
    content: str = ""
    parent_id: Optional[str] = None
    level: int = 0
    tags: List[str] = None
    created_at: str = ""
    updated_at: str = ""
    color: str = "#4ECDC4"
    size: float = 10.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class KnowledgeTree3D:
    """3D全景树管理"""

    def __init__(self, data_file="knowledge_3d.json"):
        self.data_file = data_file
        self.nodes = {}
        self._color_palette = [
            "#FF6B6B", "#4ECDC4", "#95E1D3", "#FCE38A",
            "#F38181", "#A8E6CF", "#000000", "#000000"
        ]
        self.load()

        if not self.nodes:
            self._create_default_tree()

    def _create_default_tree(self):
        """创建默认的示例树"""
        root_id = self.add_node("我的全景宇宙", "一切全景的起点", None, ["root"])

        # 第一层分支
        branches = [
            ("技术栈", "编程语言、框架、工具", ["tech"]),
            ("学习方法", "如何高效学习", ["study", "method"]),
            ("项目经验", "实际项目总结", ["project"]),
            ("生活感悟", "日常思考与反思", ["life", "thought"])
        ]

        for name, content, tags in branches:
            branch_id = self.add_node(name, content, root_id, tags)

            # 为技术分支添加子节点示例
            if name == "技术栈":
                sub_tech = [
                    ("Python", "数据分析、Web开发", ["python", "backend"]),
                    ("JavaScript", "前端开发", ["js", "frontend"]),
                    ("数据库", "SQL/NoSQL", ["database"]),
                    ("机器学习", "AI相关技术", ["ai", "ml"])
                ]
                for sub_name, sub_content, sub_tags in sub_tech:
                    self.add_node(sub_name, sub_content, branch_id, sub_tags)

    def add_node(self, name, content="", parent_id=None, tags=None):
        """添加新节点"""
        node_id = str(uuid.uuid4())

        # 计算层级和位置
        level = 0
        if parent_id and parent_id in self.nodes:
            parent = self.nodes[parent_id]
            level = parent.level + 1
            # 在父节点周围球面分布
            x, y, z = self._calculate_position(parent, level)
        else:
            x, y, z = 0, 0, 0

        node = KnowledgeNode(
            id=node_id,
            name=name,
            content=content,
            parent_id=parent_id,
            level=level,
            tags=tags or [],
            color=self._color_palette[level % len(self._color_palette)],
            size=max(20 - level * 2, 5),  # 随层级减小
            x=x,
            y=y,
            z=z
        )

        self.nodes[node_id] = node
        self.save()
        return node_id

    def _calculate_position(self, parent, level):
        """计算3D位置（球面坐标）"""
        # 获取当前父节点的子节点数
        siblings = [n for n in self.nodes.values() if n.parent_id == parent.id]
        sibling_count = len(siblings)

        # 球面坐标参数
        radius = 5 + level * 2  # 半径随层级增加
        golden_angle = np.pi * (3 - np.sqrt(5))  # 黄金角度，均匀分布

        # 使用斐波那契球面算法获得均匀分布
        theta = golden_angle * sibling_count
        z = 1 - (sibling_count / (len(self.nodes) + 1)) * 2  # z在[-1, 1]之间
        radius_xy = np.sqrt(1 - z * z)

        x = parent.x + radius * radius_xy * np.cos(theta)
        y = parent.y + radius * radius_xy * np.sin(theta)
        z = parent.z + radius * z

        return x, y, z

    def update_node(self, node_id, **kwargs):
        """更新节点"""
        if node_id in self.nodes:
            for key, value in kwargs.items():
                if hasattr(self.nodes[node_id], key):
                    setattr(self.nodes[node_id], key, value)
            self.nodes[node_id].updated_at = datetime.now().isoformat()
            self.save()
            return True
        return False

    # 在 knowledge_tree.py 的 KnowledgeTree3D 类中添加：

    def update_node_content(self, node_id, name=None, content=None, tags=None):
        """更新节点内容"""
        if node_id in self.nodes:
            node = self.nodes[node_id]

            if name is not None:
                node.name = name
            if content is not None:
                node.content = content
            if tags is not None:
                # 确保tags是列表格式
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
                node.tags = tags

            node.updated_at = datetime.now().isoformat()
            self.save()
            return True
        return False

    def delete_node(self, node_id):
        """删除节点及其子树"""
        if node_id not in self.nodes:
            return False

        # 递归查找所有子节点
        to_delete = []
        stack = [node_id]

        while stack:
            current = stack.pop()
            to_delete.append(current)
            # 查找子节点
            children = [n.id for n in self.nodes.values()
                        if n.parent_id == current]
            stack.extend(children)

        # 删除所有相关节点
        for nid in to_delete:
            del self.nodes[nid]

        self.save()
        return True

    def search_nodes(self, keyword):
        """搜索节点"""
        keyword = keyword.lower()
        results = []
        for node in self.nodes.values():
            if (keyword in node.name.lower() or
                    keyword in node.content.lower() or
                    any(keyword in tag.lower() for tag in node.tags)):
                results.append(node.id)
        return results

    def get_graph_data(self, highlight_ids=None):
        """生成3D可视化数据"""
        if not self.nodes:
            return {'nodes': {}, 'edges': {'x': [], 'y': [], 'z': [], 'colors': []}}

        nodes = list(self.nodes.values())

        # 节点数据
        node_data = {
            'x': [], 'y': [], 'z': [],
            'text': [], 'size': [], 'color': [],
            'ids': [], 'names': [], 'levels': []
        }

        # 创建节点ID到索引的映射
        node_id_to_index = {}

        for idx, node in enumerate(nodes):
            node_data['x'].append(node.x)
            node_data['y'].append(node.y)
            node_data['z'].append(node.z)
            node_data['text'].append(
                f"<b>{node.name}</b><br>"
                f"层级: {node.level}<br>"
                f"标签: {', '.join(node.tags) if node.tags else '无'}<br>"
                f"创建: {node.created_at[:10]}"
            )
            node_data['size'].append(node.size)

            # 高亮显示
            if highlight_ids and node.id in highlight_ids:
                node_data['color'].append("#95E1D3")  # 金色高亮
            else:
                node_data['color'].append(node.color)

            node_data['ids'].append(node.id)
            node_data['names'].append(node.name)
            node_data['levels'].append(node.level)
            node_id_to_index[node.id] = idx

        # 边数据（连接线） - 每条线都有对应的颜色
        edge_x, edge_y, edge_z, edge_colors = [], [], [], []

        for node in nodes:
            if node.parent_id and node.parent_id in self.nodes:
                parent = self.nodes[node.parent_id]

                # 添加直线：从子节点到父节点
                edge_x.extend([node.x, parent.x, None])
                edge_y.extend([node.y, parent.y, None])
                edge_z.extend([node.z, parent.z, None])

                # 关键：使用父节点的颜色，并调整透明度
                parent_color = parent.color

                # 将十六进制颜色转换为RGBA格式，并添加透明度
                if parent_color.startswith('#'):
                    # 十六进制转RGBA，设置透明度为0.7
                    edge_colors.extend([
                        self._hex_to_rgba(parent_color, 0.7),
                        self._hex_to_rgba(parent_color, 0.7),
                        self._hex_to_rgba(parent_color, 0.0)  # None对应的透明色
                    ])
                else:
                    # 如果是RGBA格式，直接使用
                    edge_colors.extend([parent_color, parent_color, parent_color])

        return {
            'nodes': node_data,
            'edges': {
                'x': edge_x, 'y': edge_y, 'z': edge_z,
                'colors': edge_colors  # 新增颜色数据
            }
        }

    def _hex_to_rgba(self, hex_color, alpha=0.9, is_line=True):
        """将十六进制颜色转换为RGBA格式，线条颜色增强对比度"""
        hex_color = hex_color.lstrip('#')

        # 获取基础RGB值
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        elif len(hex_color) == 3:
            r = int(hex_color[0] * 2, 16)
            g = int(hex_color[1] * 2, 16)
            b = int(hex_color[2] * 2, 16)
        else:
            r, g, b = 100, 100, 100

        # 🔧 关键：如果是线条，加深颜色增加对比度
        if is_line:
            # 计算亮度
            brightness = 0.299 * r + 0.587 * g + 0.114 * b

            # 如果颜色太浅（在白色背景下不清晰），加深颜色
            if brightness > 180:  # 亮度阈值
                # 加深颜色：减少RGB值
                darken_factor = 0.6  # 加深60%
                r = int(r * darken_factor)
                g = int(g * darken_factor)
                b = int(b * darken_factor)

            # 增加饱和度
            r, g, b = self._increase_saturation(r, g, b, factor=1.3)

            # 线条使用更高的不透明度
            alpha = min(alpha + 0.15, 0.95)

        return f'rgba({r}, {g}, {b}, {alpha})'

    def _increase_saturation(self, r, g, b, factor=1.3):
        """增加颜色饱和度"""
        # 转换为HSL调整饱和度
        r_norm = r / 255.0
        g_norm = g / 255.0
        b_norm = b / 255.0

        max_val = max(r_norm, g_norm, b_norm)
        min_val = min(r_norm, g_norm, b_norm)

        # 计算亮度
        l = (max_val + min_val) / 2.0

        if max_val == min_val:
            return r, g, b  # 无色相

        # 计算饱和度
        if l < 0.5:
            s = (max_val - min_val) / (max_val + min_val)
        else:
            s = (max_val - min_val) / (2.0 - max_val - min_val)

        # 增加饱和度
        s = min(s * factor, 1.0)

        # 转换回RGB
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1 / 6: return p + (q - p) * 6 * t
            if t < 1 / 2: return q
            if t < 2 / 3: return p + (q - p) * (2 / 3 - t) * 6
            return p

        if s == 0:
            return int(l * 255), int(l * 255), int(l * 255)

        if l < 0.5:
            q = l * (1 + s)
        else:
            q = l + s - l * s

        p = 2 * l - q

        # 计算色相（简化处理，使用主要颜色分量）
        if max_val == r_norm:
            hue = (g_norm - b_norm) / (max_val - min_val)
        elif max_val == g_norm:
            hue = 2.0 + (b_norm - r_norm) / (max_val - min_val)
        else:
            hue = 4.0 + (r_norm - g_norm) / (max_val - min_val)

        hue /= 6.0
        if hue < 0: hue += 1

        # 转换为RGB
        t_r = hue + 1 / 3
        t_g = hue
        t_b = hue - 1 / 3

        r_new = hue_to_rgb(p, q, t_r)
        g_new = hue_to_rgb(p, q, t_g)
        b_new = hue_to_rgb(p, q, t_b)

        return int(r_new * 255), int(g_new * 255), int(b_new * 255)

    def save(self):
        """保存到JSON文件"""
        data = {
            'nodes': {k: asdict(v) for k, v in self.nodes.items()}
        }
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存失败: {e}")

    def load(self):
        """从JSON文件加载"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.nodes = {}
                for node_id, node_dict in data['nodes'].items():
                    self.nodes[node_id] = KnowledgeNode(**node_dict)
        except FileNotFoundError:
            self.nodes = {}
        except Exception as e:
            print(f"加载失败: {e}")
            self.nodes = {}

    def get_stats(self):
        """获取统计信息"""
        total = len(self.nodes)
        levels = [node.level for node in self.nodes.values()]
        max_level = max(levels) if levels else 0
        avg_level = np.mean(levels) if levels else 0

        # 收集所有标签
        all_tags = []
        for node in self.nodes.values():
            all_tags.extend(node.tags)
        unique_tags = len(set(all_tags))

        return {
            'total_nodes': total,
            'max_depth': max_level,
            'avg_depth': round(avg_level, 1),
            'unique_tags': unique_tags,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
        }