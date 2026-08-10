# moving-points
通过 Movebase3D HTTP API 查询地图点位，并控制机器人导航到指定固定点位。
程序通过 HTTP API 查询机器人地图中保存的点位，并按点位名称或 ID 下发导航任务。
  路径规划、避障和底盘控制由机器人内部导航系统完成。

  ## 功能

  - 检查机器人 Web API 是否可访问
  - 查询指定地图中的固定点位
  - 按点位名称导航
  - 按点位 ID 导航
  - 支持 HTTP Basic 认证
  - 使用 Python 标准库，无需安装第三方依赖
  - 显示接口错误和导航任务下发结果

  ## 运行环境

  - Python 3.10 或更高版本
  - 能够访问机器人 Web API
  - 机器人已完成建图并保存导航点位
  - 机器人处于导航模式且定位正确

  ## 使用方法

  ### 查看帮助

  ```bash
  python3 robot_point_nav.py --help

  ### 查看地图中的点位

  python3 robot_point_nav.py \
    --host http://ROBOT_IP:9000 \
    --username USERNAME \
    --password PASSWORD \
    --map MAP_NAME \
    --list

  ### 按点位名称导航

  python3 robot_point_nav.py \
    --host http://ROBOT_IP:9000 \
    --username USERNAME \
    --password PASSWORD \
    --map MAP_NAME \
    TARGET_POINT_NAME

  ### 按点位 ID 导航

  python3 robot_point_nav.py \
    --host http://ROBOT_IP:9000 \
    --username USERNAME \
    --password PASSWORD \
    POINT_ID

  ## 示例

  查看“走点测试”地图中的点位：

  python3 robot_point_nav.py \
    --host http://192.168.0.51:9000 \
    --username admin \
    --password YOUR_PASSWORD \
    --map 走点测试 \
    --list

  导航到固定点位 A：

  python3 robot_point_nav.py \
    --host http://192.168.0.51:9000 \
    --username admin \
    --password YOUR_PASSWORD \
    --map 走点测试 \
    固定点位A

  导航到固定点位 B：

  python3 robot_point_nav.py \
    --host http://192.168.0.51:9000 \
    --username admin \
    --password YOUR_PASSWORD \
    --map 走点测试 \
    固定点位B

  ## 使用的 API

   方法    接口                   用途
  ━━━━━━  ━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━
   GET     /health                检查服务状态
  ──────  ─────────────────────  ────────────────
   GET     /api/map/point/list    查询地图点位
  ──────  ─────────────────────  ────────────────
   GET     /api/map/nav_point     导航到指定点位

  ## 工作流程

  1. 调用 /health 检查机器人服务。
  2. 调用 /api/map/point/list 获取点位列表。
  3. 根据点位名称或 ID 查找目标点位。
  4. 调用 /api/map/nav_point?pointId=... 下发导航任务。
  5. 打印服务器返回的任务下发结果。

  ## 安全注意事项

  运行导航命令前必须确认：

  - 当前加载了正确的地图。
  - 机器人处于导航模式。
  - Web 地图中的机器人位置和朝向与现场一致。
  - 激光点云与地图轮廓基本重合。
  - 急停已释放且随时可用。
  - 机器人周围和行驶路径内没有人员或危险障碍物。

  程序显示“导航任务已下发”只表示服务器接受了请求，不代表机器人已经到达目标点。

  当前版本不会：

  - 自动切换地图
  - 自动执行重定位
  - 判断定位置信度
  - 持续监控导航结果
  - 自动取消异常导航

  请勿在定位错误或未经现场安全确认的情况下运行导航命令。
