#!/usr/bin/env python3
"""通过 Movebase3D HTTP API 让机器人导航到已保存点位。"""

import argparse
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


class RobotAPI:
    def __init__(self, host: str, username: str | None, password: str | None):
        self.base_url = host.rstrip("/")
        self.headers = {"Accept": "application/json"}
        if username is not None:
            token = base64.b64encode(f"{username}:{password or ''}".encode()).decode()
            self.headers["Authorization"] = f"Basic {token}"

    def get(self, path: str, **query):
        query_string = urllib.parse.urlencode(
            {key: value for key, value in query.items() if value is not None}
        )
        url = f"{self.base_url}{path}"
        if query_string:
            url += f"?{query_string}"

        request = urllib.request.Request(url, headers=self.headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"无法连接机器人服务：{exc.reason}") from exc

    def health(self):
        return self.get("/health")

    def list_points(self, map_name: str | None = None):
        result = self.get("/api/map/point/list", mapName=map_name)
        if result.get("success") is False:
            raise RuntimeError(result.get("message") or result.get("msg") or "查询点位失败")
        data = result.get("data", result)
        if isinstance(data, list):
            return data
        for key in ("list", "points", "items", "rows"):
            if isinstance(data, dict) and isinstance(data.get(key), list):
                return data[key]
        raise RuntimeError(f"无法识别点位列表格式：{json.dumps(result, ensure_ascii=False)}")

    def navigate_to_point(self, point_id):
        result = self.get("/api/map/nav_point", pointId=point_id)
        if result.get("success") is False:
            raise RuntimeError(result.get("message") or result.get("msg") or "导航任务下发失败")
        return result


def point_name(point: dict):
    for key in ("pointName", "name", "point_name"):
        if point.get(key) is not None:
            return str(point[key])
    return ""


def point_id(point: dict):
    for key in ("id", "pointId", "point_id"):
        if point.get(key) is not None:
            return point[key]
    return None


def resolve_point(api: RobotAPI, target: str, map_name: str | None):
    points = api.list_points(map_name)
    for point in points:
        if point_name(point) == target or str(point_id(point)) == target:
            return point
    available = ", ".join(
        f"{point_name(p)}(id={point_id(p)})" for p in points
    ) or "无"
    raise RuntimeError(f"找不到点位 {target!r}。现有点位：{available}")


def build_parser():
    parser = argparse.ArgumentParser(description="控制机器人导航到已保存点位")
    parser.add_argument("target", nargs="?", help="目标点位名称或 ID")
    parser.add_argument("--host", default="http://127.0.0.1:9000", help="Web API 地址")
    parser.add_argument("--username", help="HTTP Basic 用户名")
    parser.add_argument("--password", help="HTTP Basic 密码")
    parser.add_argument("--map", dest="map_name", help="地图名称（同名点位时建议指定）")
    parser.add_argument("--list", action="store_true", help="列出点位，不移动机器人")
    return parser


def main():
    args = build_parser().parse_args()
    api = RobotAPI(args.host, args.username, args.password)

    try:
        api.health()
        points = api.list_points(args.map_name)
        if args.list:
            for point in points:
                print(f"{point_name(point):<20} id={point_id(point)}")
            return 0

        if not args.target:
            raise RuntimeError("请提供目标点位名称或 ID，或使用 --list 查看点位")

        point = resolve_point(api, args.target, args.map_name)
        result = api.navigate_to_point(point_id(point))
        print(f"导航任务已下发：{point_name(point)} (id={point_id(point)})")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
