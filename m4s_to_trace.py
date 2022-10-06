import os
import re
import json
import csv
import numpy as np
from _ctypes import PyObj_FromPtr

'''
用于读取m4s的目录生成video_meta_data
'''
VIDEO_NAME = "1-5-TahitiSurf"
TILE_NUM = 64
SEGMENT_DURATION_MS = 1000
BITRATE_KBPS = [50, 150, 250, 400, 550, 750]
BITRATE_KBPS_LOW = [50, 150, 250]  # kbps
BITRATE_KBPS_HIGH = [400, 550, 750]  # kbps

BITRATE_LEVEL = len(BITRATE_KBPS_LOW)


def get_tile_size(inputPath: str):
    '''
    读取m4s文件的大小，获得各个tile的码率
    :param path: dash m4s文件的存储路径
    :return: 保存每个tile大小的数组
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
    def take_num(elem):
        if elem[13] == '-':
            return int(elem[12:13])
        elif elem[14] == '-':
            return int(elem[12:14])
        elif elem[15] == '-':
            return int(elem[12:15])

    # tile_stream_list.sort(key=lambda x: int(x[12:13] if x[13] == '-' else x[12:14]))
    tile_stream_list.sort(key=take_num)
    print(tile_stream_list)

    segment_num = len(tile_stream_list) / (TILE_NUM * BITRATE_LEVEL)
    # print("segment_num = " + str(segment_num))

    segment_per_bitrate = []
    bitrate_per_tile = []
    for idx, tilename in enumerate(tile_stream_list):
        fileSize = os.path.getsize(os.path.join(inputPath, tilename)) * 8  # bps
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
    return sizeList


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
    with open(outputPath + VIDEO_NAME + ".json", 'w') as json_file:
        json_file.write(movie360_json_data)
    return


def generate_video_trace_csv(size_of_tile, outputPath):
    '''将tile size写入csv文件中'''
    header = ["segment", "tile"]
    for i in range(len(BITRATE_KBPS)):
        header.append("level_" + str(i))

    with open(outputPath + VIDEO_NAME + ".csv", 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(header)
        for i in range(len(size_of_tile)):
            for j in range(len(size_of_tile[0])):
                tmp = [i, j]
                tmp += size_of_tile[i][j]
                # tmp.append(size_of_tile[i][j][:])
                writer.writerow(tmp)
            # writer.writerow()
    return


# todo：改成命令行输入的形式
def main():
    # 1. 分别读取目录下的所有文件的大小
    inputPath_low = "F:\\360-degree video streaming\dash-360\src\main\scripts\\" + VIDEO_NAME + "\output_low"
    # inputPath_low = "F:\\360-degree video streaming\dash-360\src\main\scripts\\1-4-Conan Weird Al\output_low"
    inputPath_high = "F:\\360-degree video streaming\dash-360\src\main\scripts\\" + VIDEO_NAME + "\output_high"
    # inputPath_high = "F:\\360-degree video streaming\dash-360\src\main\scripts\\1-4-Conan Weird Al\output_high"
    print("inputPath_low : ", inputPath_low)
    print("inputPath_high : ", inputPath_high)
    size_of_tile_low = get_tile_size(inputPath_low)
    size_of_tile_high = get_tile_size(inputPath_high)

    # 2. 合并
    size_of_tile = np.concatenate((size_of_tile_low, size_of_tile_high), axis=2)
    size_of_tile = size_of_tile.tolist()

    # print(size_of_tile)
    # 3. 生成含video trace的movie360.json文件
    outputPath = "video_trace/"
    generate_video_trace_json(size_of_tile, outputPath)
    # 4. 生成csv文件
    generate_video_trace_csv(size_of_tile, outputPath)


if __name__ == '__main__':
    main()
