import json

'''
用于生成tile-based编码需要的config.json
'''

FRAME_RATE = 29
ORIGIN_WIDTH = 2560
ORIGIN_HEIGHT = 1440

TILE_NUM_IN_WIDTH = 8
TILE_NUM_IN_HEIGHT = 8

TARGET_BITRATE = [50, 150, 250, 400, 550, 750]  # kbps


def generate_tile_info() -> dict:
    tile_total_num = TILE_NUM_IN_WIDTH * TILE_NUM_IN_HEIGHT
    tile_width = int(ORIGIN_WIDTH / TILE_NUM_IN_WIDTH)
    tile_height = int(ORIGIN_HEIGHT / TILE_NUM_IN_HEIGHT)

    tile_info = dict()  # 含"tiles"&"qualities"&"qualities"&"srd_values"&"keyint"&"keyint_min"
    # tile位置信息设置
    tiles = []
    for i in range(TILE_NUM_IN_HEIGHT):
        for j in range(TILE_NUM_IN_WIDTH):
            tile_spatial_info = dict()
            tile_spatial_info["left"] = j * tile_width
            tile_spatial_info["top"] = i * tile_height
            tile_spatial_info["width"] = tile_width
            tile_spatial_info["height"] = tile_height

            tiles.append(tile_spatial_info)
    tile_info["tiles"] = tiles

    # 多级码率设置
    qualities = dict()
    for i, value in enumerate(TARGET_BITRATE):
        quality_per_level = dict()
        quality_per_level["resolutions"] = str(tile_width) + "x" + str(tile_height)
        quality_per_level["bitrates"] = str(value) + "k"
        qualities["level_" + str(i)] = quality_per_level
    tile_info["qualities"] = qualities

    # 空间描述符SRD
    srd_values = []
    for i in range(TILE_NUM_IN_HEIGHT):
        for j in range(TILE_NUM_IN_WIDTH):
            srd_val = [0, j, i, 1, 1, TILE_NUM_IN_WIDTH, TILE_NUM_IN_HEIGHT]
            str_val_str = str(srd_val)
            srd_values.append(str_val_str[1:-1])
    tile_info["srd_values"] = srd_values

    # 关键帧的最大和最小间隔
    tile_info["keyint"] = FRAME_RATE
    tile_info["keyint_min"] = FRAME_RATE

    return tile_info


def write_to_json(tile_info: dict, output_path: str) -> None:
    tile_info_json_data = json.dumps(tile_info, indent=4, separators=(',', ':'))
    output_file_name = output_path + 'config_8x8.json'
    with open(output_file_name, 'w') as json_file:
        json_file.write(tile_info_json_data)


def main():
    output_path = "tile_coding_config/"  # 文件的上层目录
    tile_info = generate_tile_info()
    write_to_json(tile_info, output_path)


if __name__ == '__main__':
    main()
