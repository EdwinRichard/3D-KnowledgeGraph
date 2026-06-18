import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import numpy as np
from datetime import datetime

# 导入全景树类
from knowledge_tree import KnowledgeTree3D

# 初始化应用
app = dash.Dash(
    __name__,
    title="Willow全谱捏",
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True
)

# 初始化全景树
knowledge_tree = KnowledgeTree3D()

# 应用布局
app.layout = dbc.Container([
    # 标题区
    dbc.Row([
        dbc.Col([
            html.H1("🌐 Willow全景图谱", className="mt-4 mb-3 text-primary"),
            html.P("窥一知万",
                   className="text-muted lead")
        ], width=12)
    ], className="mb-4"),

    # 主内容区
    dbc.Row([
        # 左侧控制面板
        dbc.Col([
            # 添加节点卡片
            dbc.Card([
                dbc.CardHeader("➕ 添加谱节点", className="bg-primary text-white"),
                dbc.CardBody([
                    dbc.Input(
                        id="node-name-input",
                        placeholder="谱名称 (必填)",
                        type="text",
                        className="mb-3"
                    ),
                    dbc.Textarea(
                        id="node-content-input",
                        placeholder="详细描述...",
                        rows=3,
                        className="mb-3"
                    ),
                    dbc.Input(
                        id="node-tags-input",
                        placeholder="标签 (用逗号分隔)",
                        type="text",
                        className="mb-3"
                    ),
                    dbc.Select(
                        id="parent-select",
                        options=[{"label": "🌍 作为根节点", "value": "root"}],
                        value="root",
                        className="mb-4"
                    ),
                    dbc.Button(
                        "✨ 创建节点",
                        id="create-node-btn",
                        color="primary",
                        className="w-100",
                        n_clicks=0
                    )
                ])
            ], className="mb-4"),


            # 应用布局中，在添加节点卡片后面，统计信息卡片前面添加：

            # 编辑节点卡片（初始隐藏）
            dbc.Card([
                dbc.CardHeader("✏️ 编辑选中节点", className="bg-warning text-dark"),
                dbc.CardBody([
                    dbc.Input(
                        id="edit-name-input",
                        placeholder="节点名称",
                        type="text",
                        className="mb-3"
                    ),
                    dbc.Textarea(
                        id="edit-content-input",
                        placeholder="详细描述...",
                        rows=3,
                        className="mb-3"
                    ),
                    dbc.Input(
                        id="edit-tags-input",
                        placeholder="标签 (用逗号分隔)",
                        type="text",
                        className="mb-3"
                    ),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "💾 保存修改",
                                id="save-edit-btn",
                                color="warning",
                                className="w-100"
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Button(
                                "❌ 取消",
                                id="cancel-edit-btn",
                                color="secondary",
                                className="w-100",
                                outline=True
                            )
                        ], width=6)
                    ])
                ]),
                dbc.CardFooter(id="edit-node-info", className="text-muted small")
            ], id="edit-card", style={"display": "none"}, className="mb-4"),


            # 统计信息卡片
            dbc.Card([
                dbc.CardHeader("📊 全景图谱统计", className="bg-info text-white"),
                dbc.CardBody(id="stats-display")
            ], className="mb-4"),

            # 操作卡片
            dbc.Card([
                dbc.CardHeader("⚙️ 操作", className="bg-secondary text-white"),
                dbc.CardBody([
                    dbc.ButtonGroup([
                        dbc.Button("💾 保存", id="save-btn", color="success",
                                   className="me-2", outline=True),
                        dbc.Button("🗑️ 删除选中", id="delete-btn", color="danger",
                                   outline=True),
                    ], className="w-100 mb-3"),
                    dbc.InputGroup([
                        dbc.Input(id="search-input", placeholder="搜索节点..."),
                        dbc.Button("🔍", id="search-btn", color="primary")
                    ]),
                    html.Div(id="search-results", className="mt-3")
                ])
            ])
        ], width=3),

        # 右侧可视化区
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(
                    html.Div([
                        "🎯 全景谱",
                        dbc.Badge("可旋转/缩放", color="light", className="ms-2")
                    ]),
                    className="bg-dark text-white"
                ),
                dbc.CardBody([
                    dcc.Graph(
                        id="3d-knowledge-graph",
                        style={'height': '700px'},
                        config={
                            'displayModeBar': True,
                            'scrollZoom': True,
                            'modeBarButtonsToAdd': [
                                'drawline',
                                'drawopenpath',
                                'eraseshape'
                            ]
                        }
                    ),
                    html.Div([
                        dbc.Button("🔄 重置视图", id="reset-view-btn",
                                   color="light", size="sm", className="me-2"),
                        dbc.Button("📷 截图", id="screenshot-btn",
                                   color="light", size="sm")
                    ], className="text-end mt-2")
                ])
            ]),

            # 节点详情卡片
            dbc.Card([
                dbc.CardHeader("📝 节点详情", className="bg-light"),
                dbc.CardBody(id="node-detail-content")
            ], className="mt-4")
        ], width=9)
    ]),

    # 存储组件
    dcc.Store(id='selected-node-store'),
    dcc.Store(id='graph-data-store'),
    dcc.Store(id='search-results-store'),

    # 自动保存间隔
    dcc.Interval(id='auto-save-interval', interval=300000),  # 60秒自动保存

    # 通知组件
    dbc.Toast(
        id="notification-toast",
        header="通知",
        is_open=False,
        dismissable=True,
        duration=4000,
        style={"position": "fixed", "top": 10, "right": 10, "width": 350}
    )
], fluid=True, className="px-4")


# ========== 回调函数 ==========

@callback(
    Output("parent-select", "options"),
    [Input("3d-knowledge-graph", "clickData"),
     Input("create-node-btn", "n_clicks"),
     Input("delete-btn", "n_clicks")]
)
def update_parent_options(click_data, n_clicks_create, n_clicks_delete):
    """更新父节点选择下拉框（按层级和创建时间排序）"""
    options = [{"label": "🌍 作为根节点", "value": "root"}]

    # 如果没有节点，返回基本选项
    if not knowledge_tree.nodes:
        return options

    # ========== 核心算法：按层级和创建时间排序 ==========

    def build_hierarchical_options():
        """构建层级化的选项列表"""

        # 1. 首先找出所有根节点（parent_id为None）
        root_nodes = [node for node in knowledge_tree.nodes.values()
                      if node.parent_id is None]

        # 2. 根节点按创建时间排序（新的在前）
        root_nodes.sort(key=lambda n: n.created_at)

        all_options = []

        def add_node_with_children(node, depth=0):
            """递归添加节点及其子节点"""
            # 计算缩进
            indent = " " * depth

            # 选择图标
            if depth == 0:
                icon = "🌳"  # 根节点
            elif depth == 1:
                icon = "🌿"  # 一级子节点
            elif depth == 2:
                icon = "🍃"  # 二级子节点
            else:
                icon = "📄"  # 更深层节点

            # 创建时间格式化为可读形式
            try:
                create_time = datetime.fromisoformat(node.created_at.replace('Z', '+00:00'))
                time_str = create_time.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = node.created_at[:16] if len(node.created_at) >= 16 else node.created_at

            # 添加当前节点
            all_options.append({
                "label": f"{indent}{icon} {node.name} [{time_str}]",
                "value": node.id,
                "level": depth,
                "created_at": node.created_at
            })

            # 3. 获取当前节点的子节点
            children = [n for n in knowledge_tree.nodes.values()
                        if n.parent_id == node.id]

            # 4. 子节点按创建时间排序（新的在前）
            children.sort(key=lambda n: n.created_at, reverse=False)

            # 5. 递归添加子节点
            for child in children:
                add_node_with_children(child, depth + 1)

        # 从每个根节点开始递归构建
        for root in root_nodes:
            add_node_with_children(root, 0)

        return all_options

    # 构建排序后的选项
    sorted_options = build_hierarchical_options()

    # 添加到最终选项列表
    for item in sorted_options:
        options.append({
            "label": item["label"],
            "value": item["value"]
        })

    return options


@callback(
    [Output("3d-knowledge-graph", "figure"),
     Output("graph-data-store", "data"),
     Output("stats-display", "children")],
    [Input("create-node-btn", "n_clicks"),
     Input("delete-btn", "n_clicks"),
     Input("search-btn", "n_clicks"),
     Input("reset-view-btn", "n_clicks"),
     Input("save-edit-btn", "n_clicks"),  # 新增：编辑保存触发
     Input("auto-save-interval", "n_intervals")],
    [State("node-name-input", "value"),
     State("node-content-input", "value"),
     State("node-tags-input", "value"),
     State("parent-select", "value"),
     State("search-input", "value"),
     State("selected-node-store", "data")],
    prevent_initial_call=True
)
def update_graph(n_create, n_delete, n_search, n_reset, n_save_edit, n_interval,
                 name, content, tags, parent_id, search_query, selected_id):
    """更新3D图形"""
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # 处理创建节点
    if triggered_id == "create-node-btn" and name:
        tags_list = [t.strip() for t in tags.split(",")] if tags else []
        actual_parent = None if parent_id == "root" else parent_id
        knowledge_tree.add_node(name, content or "", actual_parent, tags_list)

    # 处理删除节点
    elif triggered_id == "delete-btn" and selected_id:
        knowledge_tree.delete_node(selected_id)
        selected_id = None

    # 处理搜索
    highlight_ids = []
    if triggered_id == "search-btn" and search_query:
        highlight_ids = knowledge_tree.search_nodes(search_query)

    # 获取图形数据
    graph_data = knowledge_tree.get_graph_data(highlight_ids)

    # ... 原有的绘图代码保持不变 ...

    

    # 在 update_graph 函数中，替换创建图形的部分：

    # 创建3D图形
    fig = go.Figure()

    # 1. 先画连接线（最底层）
    # 1. 绘制连接线（每条线使用父节点颜色）
    # 1. 绘制连接线（统一使用蓝色系）
    if graph_data['edges']['x']:
        # 使用深蓝色线条，在白色背景下最清晰
        fig.add_trace(go.Scatter3d(
            x=graph_data['edges']['x'],
            y=graph_data['edges']['y'],
            z=graph_data['edges']['z'],
            mode='lines',
            line=dict(
                color='rgba(30, 80, 200, 0.7)',  # 🔵 深蓝色，高对比度
                width=3,  # 粗线条
            ),
            hoverinfo='none',
            name='谱关系',
            showlegend=False
        ))

    # 2. 添加节点的"外圈"（稍大，半透明）
    if graph_data['nodes']['x']:
        fig.add_trace(go.Scatter3d(
            x=graph_data['nodes']['x'],
            y=graph_data['nodes']['y'],
            z=graph_data['nodes']['z'],
            mode='markers',
            marker=dict(
                size=[s * 1.3 for s in graph_data['nodes']['size']],  # 外圈更大
                color=graph_data['nodes']['color'],
                line=dict(color='white', width=1),
                symbol='circle',
                opacity=0.15  # 很淡的外圈
            ),
            hoverinfo='none',
            showlegend=False
        ))

    # 3. 添加主节点（最上层，实体）
    if graph_data['nodes']['x']:
        fig.add_trace(go.Scatter3d(
            x=graph_data['nodes']['x'],
            y=graph_data['nodes']['y'],
            z=graph_data['nodes']['z'],
            mode='markers+text',
            marker=dict(
                size=graph_data['nodes']['size'],
                color=graph_data['nodes']['color'],
                line=dict(color='white', width=2.5),
                symbol='circle',
                opacity=0.95
            ),
            text=graph_data['nodes']['names'],
            textposition="top center",
            hovertext=graph_data['nodes']['text'],
            hoverinfo="text",
            customdata=graph_data['nodes']['ids'],
            name='全景节点',
            showlegend=False
        ))
    # 隐藏坐标系
    # 在创建完图形后（return 语句之前）添加以下代码：

    # ========== 关键：添加布局配置，隐藏坐标系 ==========
    fig.update_layout(
        scene=dict(
            # 完全隐藏X轴
            xaxis=dict(
                visible=False,
                showbackground=False,
                showgrid=False,
                showline=False,
                showticklabels=False,
                title='',
                zeroline=False
            ),
            # 完全隐藏Y轴
            yaxis=dict(
                visible=False,
                showbackground=False,
                showgrid=False,
                showline=False,
                showticklabels=False,
                title='',
                zeroline=False
            ),
            # 完全隐藏Z轴
            zaxis=dict(
                visible=False,
                showbackground=False,
                showgrid=False,
                showline=False,
                showticklabels=False,
                title='',
                zeroline=False
            ),
            # 设置背景（几乎透明）
            bgcolor='rgba(255, 255, 255, 0.02)',
            # 设置相机视角
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2),
                up=dict(x=0, y=0, z=1),
                projection=dict(type='perspective')
            )
        ),
        # 其他布局设置
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        hovermode='closest',
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    # 获取统计信息
    stats = knowledge_tree.get_stats()
    stats_display = dbc.ListGroup([
        dbc.ListGroupItem(f"📈 总节点数: {stats['total_nodes']}"),
        dbc.ListGroupItem(f"🌳 最大深度: {stats['max_depth']}"),
        dbc.ListGroupItem(f"📊 平均深度: {stats['avg_depth']}"),
        dbc.ListGroupItem(f"🏷️ 独特标签: {stats['unique_tags']}"),
        dbc.ListGroupItem(f"🕒 最后更新: {stats['last_updated']}")
    ], flush=True)

    return fig, graph_data, stats_display

    # 获取统计信息
    stats = knowledge_tree.get_stats()
    stats_display = dbc.ListGroup([
        dbc.ListGroupItem(f"📈 总节点数: {stats['total_nodes']}"),
        dbc.ListGroupItem(f"🌳 最大深度: {stats['max_depth']}"),
        dbc.ListGroupItem(f"📊 平均深度: {stats['avg_depth']}"),
        dbc.ListGroupItem(f"🏷️ 独特标签: {stats['unique_tags']}"),
        dbc.ListGroupItem(f"🕒 最后更新: {stats['last_updated']}")
    ], flush=True)

    return fig, graph_data, stats_display


@callback(
    [Output("node-detail-content", "children"),
     Output("selected-node-store", "data"),
     Output("edit-card", "style"),  # 新增：控制编辑卡片显示
     Output("edit-name-input", "value"),  # 新增：填充编辑表单
     Output("edit-content-input", "value"),
     Output("edit-tags-input", "value"),
     Output("edit-node-info", "children")],
    [Input("3d-knowledge-graph", "clickData"),
     Input("cancel-edit-btn", "n_clicks")],  # 新增：取消编辑按钮
    [State("graph-data-store", "data")]
)
def handle_node_click(click_data, n_cancel, graph_data):
    """处理节点点击，显示详情并存储选中ID"""
    from dash import ctx

    # 如果点击了取消按钮
    if ctx.triggered_id == "cancel-edit-btn":
        return (html.P("点击任意节点查看详情", className="text-muted"),
                None, {"display": "none"}, "", "", "", "")

    if not click_data or not graph_data:
        return (html.P("点击任意节点查看详情", className="text-muted"),
                None, {"display": "none"}, "", "", "", "")

    points = click_data.get('points', [])
    if not points:
        return (html.P("点击任意节点查看详情", className="text-muted"),
                None, {"display": "none"}, "", "", "", "")

    point_data = points[0]

    # 检查是否点击了节点（而不是线）
    if 'customdata' not in point_data:
        return (html.P("请点击节点（圆圈部分）", className="text-warning"),
                None, {"display": "none"}, "", "", "", "")

    node_id = point_data['customdata']
    node = knowledge_tree.nodes.get(node_id)

    if not node:
        return (html.P("节点数据加载失败", className="text-danger"),
                None, {"display": "none"}, "", "", "", "")

    # 获取子节点
    children = [n for n in knowledge_tree.nodes.values()
                if n.parent_id == node_id]

    # 获取父节点
    parent = knowledge_tree.nodes.get(node.parent_id) if node.parent_id else None

    # 构建详情内容
    details = [
        html.H4(f"📋 {node.name}", className="mb-3"),

        html.H6("📝 内容描述", className="mt-3"),
        html.P(node.content or "暂无详细描述", className="text-muted"),

        html.H6("🏷️ 标签", className="mt-3"),
        html.Div([
            dbc.Badge(tag, color="primary", className="me-1 mb-1",
                      pill=True) for tag in node.tags
        ]) if node.tags else html.P("无标签", className="text-muted"),

        html.Hr(),

        dbc.Row([
            dbc.Col([
                html.H6("📊 基本信息"),
                dbc.ListGroup([
                    dbc.ListGroupItem(f"层级: {node.level}"),
                    dbc.ListGroupItem(f"创建: {node.created_at[:10]}"),
                    dbc.ListGroupItem(f"更新: {node.updated_at[:10]}"),
                ], flush=True)
            ], width=6),

            dbc.Col([
                html.H6("🔗 关联信息"),
                dbc.ListGroup([
                    dbc.ListGroupItem(
                        f"父节点: {parent.name if parent else '无'}"
                    ),
                    dbc.ListGroupItem(f"子节点数: {len(children)}"),
                    dbc.ListGroupItem(f"节点ID: {node.id[:8]}..."),
                ], flush=True)
            ], width=6)
        ]),

        # 添加编辑按钮
        html.Div([
            dbc.Button(
                "✏️ 编辑此节点",
                id="start-edit-btn",
                color="warning",
                size="sm",
                className="mt-3"
            )
        ], className="text-center")
    ]

    # 准备编辑表单的数据
    edit_form_style = {"display": "none"}  # 默认隐藏编辑表单
    edit_name = node.name
    edit_content = node.content or ""
    edit_tags = ", ".join(node.tags) if node.tags else ""

    # 编辑卡片的信息
    try:
        create_time = datetime.fromisoformat(node.created_at.replace('Z', '+00:00'))
        update_time = datetime.fromisoformat(node.updated_at.replace('Z', '+00:00'))
        node_info = f"层级: {node.level} | 创建: {create_time.strftime('%Y-%m-%d')} | 更新: {update_time.strftime('%Y-%m-%d')}"
    except:
        node_info = f"层级: {node.level} | 节点ID: {node.id[:8]}..."

    return (details, node_id, edit_form_style, edit_name, edit_content, edit_tags, node_info)


@callback(
    [Output("edit-card", "style", allow_duplicate=True),
     Output("node-detail-content", "children", allow_duplicate=True)],
    Input("start-edit-btn", "n_clicks"),
    State("selected-node-store", "data"),
    prevent_initial_call=True
)
def show_edit_form(n_clicks, selected_id):
    """显示编辑表单"""
    if not n_clicks or not selected_id:
        return {"display": "none"}, no_update

    node = knowledge_tree.nodes.get(selected_id)
    if not node:
        return {"display": "none"}, no_update

    # 创建一个简单的详情视图，提示正在编辑
    details = [
        html.H4(f"✏️ 正在编辑: {node.name}", className="mb-3 text-warning"),
        html.P("请在左侧编辑表单中修改节点信息", className="text-muted"),
        html.Hr(),
        dbc.Alert("修改完成后点击'保存修改'按钮", color="warning", className="mt-3")
    ]

    return {"display": "block"}, details


@callback(
    [Output("notification-toast", "is_open", allow_duplicate=True),
     Output("notification-toast", "header", allow_duplicate=True),
     Output("notification-toast", "children", allow_duplicate=True),
     Output("edit-card", "style", allow_duplicate=True),
     Output("selected-node-store", "data", allow_duplicate=True)],
    Input("save-edit-btn", "n_clicks"),
    [State("edit-name-input", "value"),
     State("edit-content-input", "value"),
     State("edit-tags-input", "value"),
     State("selected-node-store", "data")],
    prevent_initial_call=True
)
def save_node_edits(n_clicks, name, content, tags, node_id):
    """保存节点编辑"""
    if not n_clicks or not node_id or not name:
        return False, "", "", {"display": "none"}, node_id

    # 解析标签
    tags_list = [tag.strip() for tag in tags.split(",")] if tags else []

    # 更新节点
    success = knowledge_tree.update_node_content(node_id, name, content, tags_list)

    if success:
        return (
            True,  # 显示通知
            "保存成功",
            f"节点 '{name}' 已更新",
            {"display": "none"},  # 隐藏编辑卡片
            None  # 清空选中状态，强制刷新
        )
    else:
        return (
            True,
            "保存失败",
            "节点更新失败，请重试",
            {"display": "block"},
            node_id
        )

@callback(
    Output("notification-toast", "is_open"),
    Output("notification-toast", "header"),
    Output("notification-toast", "children"),
    Input("save-btn", "n_clicks"),
    Input("auto-save-interval", "n_intervals"),
    Input("create-node-btn", "n_clicks"),
    Input("delete-btn", "n_clicks")
)
def show_notification(n_save, n_auto, n_create, n_delete):
    """显示操作通知"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", ""

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == "save-btn":
        knowledge_tree.save()
        return True, "保存成功", "全景图谱已保存到本地文件"
    elif triggered_id == "auto-save-interval":
        knowledge_tree.save()
        return True, "自动保存", "系统已自动保存您的更改"
    elif triggered_id == "create-node-btn":
        return True, "节点创建", "新全景节点已添加到图谱中"
    elif triggered_id == "delete-btn":
        return True, "节点删除", "选中节点及其子树已删除"

    return False, "", ""


@callback(
    Output("search-results", "children"),
    Input("search-results-store", "data")
)
def display_search_results(results_data):
    """显示搜索结果"""
    if not results_data or not results_data.get('results'):
        return html.P("暂无搜索结果", className="text-muted")

    results = results_data['results']
    query = results_data['query']

    items = [html.H6(f"搜索 '{query}' 结果:", className="mb-2")]

    for node_id in results[:5]:  # 最多显示5个
        node = knowledge_tree.nodes.get(node_id)
        if node:
            items.append(
                dbc.ListGroupItem([
                    html.Strong(node.name),
                    html.Small(f" (层级: {node.level})",
                               className="text-muted ms-2")
                ])
            )

    if len(results) > 5:
        items.append(html.P(f"...等 {len(results)} 个结果",
                            className="text-muted mt-2"))

    return dbc.ListGroup(items, flush=True)


@callback(
    Output("search-results-store", "data"),
    Input("search-btn", "n_clicks"),
    State("search-input", "value")
)
def perform_search(n_clicks, query):
    """执行搜索"""
    if not query:
        return {'results': [], 'query': ''}

    results = knowledge_tree.search_nodes(query)
    return {'results': results, 'query': query}


# 运行应用
if __name__ == "__main__":
    print("🚀 启动3D全景图谱应用...")
    print(f"📁 数据文件: {knowledge_tree.data_file}")
    print("🌐 请访问: http://localhost:8051")
    app.run(debug=True, port=8051)