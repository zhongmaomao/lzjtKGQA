#!/usr/bin/env python3
# coding: utf-8


import os
import py2neo
import csv
from py2neo import Graph,Node

graph = Graph('http://localhost:7474/', auth=("neo4j", "neo4j_mlx"))
#graph.delete_all()  # 删除已有的所有内容
tx=graph.begin()

class Graph:
    def __init__(self):
        self.data_path="C:/Users/El Psy/Desktop/实训/Project/Project_v1/data/data.json"
        self.data_path="E:/暂存/cowork/lzjt/lzjt_dc/lzjt_cl_xx_gjc.csv"
        #self.g = Graph('http://localhost:7474/', auth=("neo4j", "neo4j_mlx"))

    '''读取文件'''
    def read_nodes(self):
        # 节点实体
        gjc_set = []  # 公交车集合
        qy = []  # 企业
        lx = []  # 路线
        gpspt = []  # GPS平台
        gjc_info = []  # 公交车信息

        # 实体关系
        r_gjc_ssqymc = []  # 公交车－企业关系（属于）
        r_gjc_sslxmc = []  # 公交车-路线关系（属于）
        r_gjc_gpspt = []  # 公交车-gps平台关系（属于）

        with open(self.data_path, encoding='utf-8') as f:
            data_csv = csv.reader(f)
            headers = next(data_csv)
            headers_cn = ['id', '所属企业名称', '所属路线名称', '所属路线编码', '座位数', '站位数', '客定载客量', '燃油类型编码',
                          'GPS平台', '是否空调车', '是否装有车载机', '是否智能网联车', '备注', '车辆号牌', '号牌颜色', '所属企业编码']

            for row in data_csv:
                # print(row)
                # print("当前行数：", data_csv.line_num, "当前内容：", row)
                gjc = row[13]  # clhp 车辆号牌
                gjc_set.append(gjc)

                gjc_dict = dict(zip(headers_cn, row))

                # 节点
                e = gjc_dict['所属企业名称']
                if e:
                    qy.append(e)
                    r_gjc_ssqymc.append([gjc, e])  # 建立公交车－企业关系（属于）

                e = gjc_dict['所属路线名称']
                if e:
                    lx.append(e)
                    r_gjc_sslxmc.append([gjc, e])  # 建立公交车-路线关系（属于）

                e = gjc_dict['GPS平台']
                if e:
                    gpspt.append(e)
                    r_gjc_gpspt.append([gjc, e])  # 建立公交车-线路关系（属于）

                gjc_info.append(gjc_dict)  # 公交车信息

        return set(gjc_set), set(qy), set(lx), set(gpspt), gjc_info, r_gjc_gpspt, r_gjc_sslxmc, r_gjc_ssqymc


    '''建立节点'''
    def create_node(self, label, nodes):
        count = 0
        for node_name in nodes:
            node = Node(label, name=node_name)
            graph.create(node)
            count += 1
            #print(label, count, len(nodes))
        return

    '''创建公交车节点'''
    def create_gjc_nodes(self, gjc_info):
        count = 0
        for info in gjc_info:
            # node = Node("spot", name=spot_dict['name'], area=spot_dict['area'],address=spot_dict['address'],
            #             intro=spot_dict['intro'],hot=spot_dict['hot'], price=spot_dict['price'], sold=spot_dict['sold'])
            info_str=str(info)
            node=Node('车辆',name='公交车'+info['车辆号牌'],信息=info_str)
            graph.create(node)
            count += 1
            print(count)
        return

    '''创建知识图谱实体节点类型schema'''
    def create_graphnodes(self):
        gjc_set, qy, lx, gpspt, gjc_info, r_gjc_gpspt, r_gjc_sslxmc, r_gjc_ssqymc = self.read_nodes()

        self.create_gjc_nodes(gjc_info)

        self.create_node('企业', qy)
        print(len(qy))

        self.create_node('路线', lx)
        print(len(lx))

        self.create_node('GPS平台', gpspt)
        print(len(gpspt))

        return


    '''创建实体关联边'''
    def create_relationship_quchongbanben(self, start_node, end_node, edges, rel_type, rel_name):
        count = 0
        # 去重处理
        set_edges = []
        for edge in edges:
            set_edges.append('###'.join(edge))
        all = len(set(set_edges))
        for edge in set(set_edges):
            edge = edge.split('###')
            p = '公交车'+edge[0]
            q = edge[1]

            query = "match(p:%s),(q:%s) where p.name='%s'and q.name='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, p, q, rel_type, rel_name)

            try:
                #self.g.run(query)
                graph.run(query)
                count += 1
                print(rel_type, count, all)
            except Exception as e:
                print(e)

        return

    def create_relationship(self, start_node, end_node, edges, rel_type, rel_name):
        count = 0
        all=len(edges)
        for edge in edges:
            p = '公交车' + edge[0]
            q = edge[1]

            query = "match(p:%s),(q:%s) where p.name='%s'and q.name='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, p, q, rel_type, rel_name)

            try:
                # self.g.run(query)
                graph.run(query)
                count += 1
                print(rel_type, count, all)
            except Exception as e:
                print(e)

        return


    '''创建实体关系边'''
    def create_graphrels(self):
        gjc_set, qy, lx, gpspt, gjc_info, r_gjc_gpspt, r_gjc_sslxmc, r_gjc_ssqymc = self.read_nodes()

        self.create_relationship('车辆', 'GPS平台', r_gjc_gpspt, '属于', '使用')
        self.create_relationship('车辆', '路线', r_gjc_sslxmc, '属于', '所属路线名称')
        self.create_relationship('车辆', '企业', r_gjc_ssqymc, '属于', '所属企业名称')



if __name__ == '__main__':
    handler = Graph()

    #handler.create_graphnodes()
    handler.create_graphrels()
    #tx.commit()
