#!/usr/bin/env python3
import csv, math, argparse
from heap_helper import MinHeap

def hav_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))

def load_points(csv_path, lat_col, lon_col, max_rows=None):
    pts = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for i,row in enumerate(r):
            if max_rows is not None and i >= max_rows:
                break
            try:
                lat = float(row[lat_col])
                lon = float(row[lon_col])
                pts.append((lat, lon))
            except:
                pts.append((float("nan"), float("nan")))
    return pts

def valid_points(pts):
    idx = []
    clean = []
    for i,(lat,lon) in enumerate(pts):
        if lat == lat and lon == lon:
            idx.append(i)
            clean.append((lat,lon))
    return idx, clean

def build_knn_graph(pts, k):
    n = len(pts)
    g = [[] for _ in range(n)]
    for i,(lat1,lon1) in enumerate(pts):
        dists = []
        for j,(lat2,lon2) in enumerate(pts):
            if i == j:
                continue
            d = hav_km(lat1, lon1, lat2, lon2)
            dists.append((d, j))
        dists.sort(key=lambda x: x[0])
        for d,j in dists[:k]:
            g[i].append((j, d))
    return g

def dijkstra(graph, source):
    n = len(graph)
    dist = [float("inf")]*n
    prev = [-1]*n
    dist[source] = 0.0
    pq = MinHeap()
    pq.push((0.0, source))
    while len(pq) > 0:
        item = pq.pop()
        if item is None:
            break
        du,u = item
        if du > dist[u]:
            continue
        for v,w in graph[u]:
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                pq.push((nd, v))
    return dist, prev

def path_to(prev, t):
    p = []
    while t != -1:
        p.append(t)
        t = prev[t]
    p.reverse()
    return p

def nearest_idx(pts, lat, lon):
    best = -1
    bestd = float("inf")
    for i,(a,b) in enumerate(pts):
        d = hav_km(lat, lon, a, b)
        if d < bestd:
            bestd = d
            best = i
    return best

def remap_back(path, idx_map):
    return [idx_map[i] for i in path]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--lat-col", default="Latitude")
    ap.add_argument("--lon-col", default="Longitude")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--source-pid", type=int)
    ap.add_argument("--source-lat", type=float)
    ap.add_argument("--source-lon", type=float)
    ap.add_argument("--target-pid", type=int)
    ap.add_argument("--max-rows", type=int)
    args = ap.parse_args()

    raw = load_points(args.csv, args.lat_col, args.lon_col, args.max_rows)
    idx_map, pts = valid_points(raw)
    if len(pts) == 0:
        print("no valid points")
        return

    g = build_knn_graph(pts, args.k)

    if args.source_pid is not None:
        if args.source_pid not in idx_map:
            print("source pid invalid")
            return
        s = idx_map.index(args.source_pid)
    else:
        if args.source_lat is None or args.source_lon is None:
            s = 0
        else:
            s = nearest_idx(pts, args.source_lat, args.source_lon)

    dist, prev = dijkstra(g, s)
    print(f"nodes={len(pts)} k={args.k} source_idx={s} source_pid={idx_map[s]}")
    order = sorted(range(len(pts)), key=lambda i: dist[i])
    print("nearest 10 by path distance (km):")
    for i in order[:10]:
        print(f"pid={idx_map[i]} dist_km={dist[i]:.3f}")

    if args.target_pid is not None:
        if args.target_pid not in idx_map:
            print("target pid invalid")
            return
        t = idx_map.index(args.target_pid)
        p = path_to(prev, t)
        rp = remap_back(p, idx_map)
        print(f"path_len_km={dist[t]:.3f}")
        print("path_pids:", rp)

if __name__ == "__main__":
    main()
