#!/usr/bin/env python3
"""通过 Movebase3D HTTP API 让机器人导航到已保存点位。"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


class RobotAPI:
    def __init__(self, host: str, username: str | None, password: str | None):
        self.base_url = host.rstrip("/")
        self._session_cookie: str | None = None
        if username is not None:
            self._login(username, password or "")

    def _login(self, username: str, password: str):
        """POST /api/auth/login 获取 session cookie，后续请求自动携带。"""
        url = f"{self.base_url}/api/auth/login"
        data = json.dumps({"username": username, "password": password}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                # 从 Set-Cookie 响应头提取 session 值
                for header_name, header_value in response.getheaders():
                    if header_name.lower() == "set-cookie":
                        for part in header_value.split(";"):
                            part = part.strip()
                            if part.lower().startswith("session="):
                                self._session_cookie = part.split("=", 1)[1].strip()
                result = json.loads(response.read().decode("utf-8"))
                if result.get("success") is False:
                    raise RuntimeError(
                        result.get("message") or result.get("msg") or "登录失败"
                    )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"登录失败 HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"无法连接机器人服务：{exc.reason}") from exc

    def _build_headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self._session_cookie:
            headers["Cookie"] = f"session={self._session_cookie}"
        return headers

    def _request(self, method: str, path: str, data=None, **query):
        query_string = urllib.parse.urlencode(
            {key: value for key, value in query.items() if value is not None}
        )
        url = f"{self.base_url}{path}"
        if query_string:
            url += f"?{query_string}"

        request = urllib.request.Request(
            url, data=data, headers=self._build_headers(), method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"无法连接机器人服务：{exc.reason}") from exc

    def get(self, path: str, **query):
        return self._request("GET", path, **query)

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
    parser.add_argument("--username", help="登录用户名（默认无认证）")
    parser.add_argument("--password", help="登录密码")
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
