import os
import re
import json
import numpy as np
from _ctypes import PyObj_FromPtr

'''
用于读取m4s的目录生成video_meta_data
'''

TILE_NUM = 8
SEGMENT_DURATION_MS = 1000
BITRATE_KBPS = [600, 1500, 3000]
BITRATE_LEVEL = len(BITRATE_KBPS)


class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))

    def __init__(self, **kwargs):
        # Save copy of any keyword argument values needed for use here.
        self.__sort_keys = kwargs.get('sort_keys', None)
        super(MyEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, NoIndent)
                else super(MyEncoder, self).default(obj))

    def encode(self, obj):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.
        json_repr = super(MyEncoder, self).encode(obj)  # Default JSON.

        # Replace any marked-up object ids in the JSON repr with the
        # value returned from the json.dumps() of the corresponding
        # wrapped Python object.
        for match in self.regex.finditer(json_repr):
            # see https://stackoverflow.com/a/15012814/355230
            id = int(match.group(1))
            no_indent = PyObj_FromPtr(id)
            json_obj_repr = json.dumps(no_indent.value, sort_keys=self.__sort_keys)

            # Replace the matched id string with json formatted representation
            # of the corresponding Python object.
            json_repr = json_repr.replace(
                '"{}"'.format(format_spec.format(id)), json_obj_repr)

        return json_repr


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


def generate_video_trace(size, outputPath):
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
    with open(outputPath, 'w') as json_file:
        json_file.write(movie360_json_data)


# todo：改成命令行输入的形式
def main():
    # 1. 读取目录下的所有文件的大小
    inputPath = "dash_file"
    size_of_tile = get_tile_size(inputPath)
    print(size_of_tile)
    # 2. 生成含video trace的movie360.json文件
    outputPath = "video_trace/movie360.json"
    generate_video_trace(size_of_tile, outputPath)
    # todo：增加一个csv文件的写入


if __name__ == '__main__':
    main()
