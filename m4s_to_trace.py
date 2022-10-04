import os
import re
import json
import csv
import numpy as np
from _ctypes import PyObj_FromPtr

'''
用于读取m4s的目录生成video_meta_data
'''

TILE_NUM = 8
SEGMENT_DURATION_MS = 1000
BITRATE_KBPS = [600, 1500, 3000]
BITRATE_LEVEL = len(BITRATE_KBPS)


def get_tile_size(inputPath: str):
    '''
    读取m4s文件的大小，获得各个tile的码率
    :param path: dash m4s文件的存储路径
    :return: 保存每个tile大小的列表
    '''
    sizeList = []  # [tile][bitrate][segment]

    fileList = os.listdir(inputPath)
    # print(fileList)
    tile_stream_list = []
    for filename in fileList:
        if "chunk-stream" in filename:  # 只取类chunk-stream0-00003.m4s的文件
            tile_stream_list.append(filename)
    # print(tile_stream_list)

    # 对文件进行重新排序
    tile_stream_list.sort(key=lambda x: int(x[12:13] if x[13] == '-' else x[12:14]))
    # print(tile_stream_list)

    segment_num = len(tile_stream_list) / (TILE_NUM * BITRATE_LEVEL)
    # print("segment_num = " + str(segment_num))

    segment_per_bitrate = []
    bitrate_per_tile = []
    for idx, tilename in enumerate(tile_stream_list):
        fileSize = os.path.getsize(os.path.join(inputPath, tilename))
        segment_per_bitrate.append(fileSize)
        if len(segment_per_bitrate) == segment_num:
            bitrate_per_tile.append(segment_per_bitrate[:])
            segment_per_bitrate = []
        if len(bitrate_per_tile) == BITRATE_LEVEL:
            sizeList.append(bitrate_per_tile[:])
            bitrate_per_tile = []
    sizeList = np.array(sizeList)
    sizeList = sizeList.transpose(2, 0, 1)  # [segment][tile][bitrate]
    # print(sizeList)
    return sizeList.tolist()


def generate_video_trace_json(size, outputPath):
    '''
    生成含video trace的movie360.json文件
    :param size: 保存每个tile大小的列表
    :param outputPath: 保存video trace的路径
    :return:
    '''
    video_trace_dict = dict()
    video_trace_dict["segment_duration_ms"] = SEGMENT_DURATION_MS
    video_trace_dict["tiles"] = TILE_NUM
    video_trace_dict["bitrates_kbps"] = BITRATE_KBPS
    video_trace_dict["_comment_"] = "segment_sizes_bits[segment_index][tile_index][bitrate_index]"
    video_trace_dict["segment_sizes_bits"] = size

    movie360_json_data = json.dumps(video_trace_dict, indent=4, separators=(',', ':'))
    # movie360_json_data = json.dumps(video_trace_dict)
    with open(outputPath + "movie360.json", 'w') as json_file:
        json_file.write(movie360_json_data)
    return


def generate_video_trace_csv(size_of_tile, outputPath):
    '''将tile size写入csv文件中'''
    header = []
    for i in range(len(BITRATE_KBPS)):
        header.append("level_" + str(i))

    with open(outputPath + "movie360.csv", 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(header)
        for i in range(len(size_of_tile)):
            writer.writerow(size_of_tile[i])
            writer.writerow()


# todo：改成命令行输入的形式
def main():
    # 1. 读取目录下的所有文件的大小
    inputPath = "dash_file"
    size_of_tile = get_tile_size(inputPath)
    print(size_of_tile)
    # 2. 生成含video trace的movie360.json文件
    outputPath = "video_trace/"
    generate_video_trace_json(size_of_tile, outputPath)
    # todo：增加一个csv文件的写入
    generate_video_trace_csv(size_of_tile, outputPath)


if __name__ == '__main__':
    main()
