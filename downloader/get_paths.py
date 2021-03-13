from webdav3.client import Client
from htutil import file
import yaml


def is_dir(path: str):
    return path[-1] == '/'


def list_all_paths(client, path_dir: str):
    paths = client.list(path_dir)
    del paths[0]
    for i in range(len(paths)):
        paths[i] = f'{path_dir}/{paths[i]}'
    for path in paths:
        if is_dir(path):
            child_path = list_all_paths(client, path)
            paths.extend(child_path)
    return paths


def upload():
    hostname = config['webdav']['hostname']
    option = {
        'webdav_hostname': hostname,
        'webdav_login': config['webdav']['username'],
        'webdav_password': config['webdav']['password'],
        'disable_check': True,  # 有的网盘不支持check功能
    }

    client = Client(option)

    av_min_size = 500 * 1024 * 1024  # size of av should > 500 MB

    paths = list_all_paths(client, '/')
    av_paths = []

    for path in paths:
        info = client.info(path)
        if info['size'] is not None:
            size = int(info['size'])
            if size > av_min_size:
                url = f'{hostname}/{path}'
                url = url.replace('///','/')
                av_paths.append(url)
                print(path)

    file.write_all_lines('paths.txt', av_paths)


if __name__ == '__main__':
    config = yaml.load(file.read_all_text('config.yaml'), Loader=yaml.SafeLoader)
    upload()
