from htutil import file
import yaml
import requests
from tqdm import tqdm
import os
from htutil.log import p
from htutil import log
from urllib import parse
from func_timeout import func_set_timeout
from func_timeout.exceptions import FunctionTimedOut
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import datetime


def append_to_log(line):
    file.append_all_lines('download.log', [line+'\n'])


@func_set_timeout(15)
def download(file_name, response, bar):
    with open(file_name, "ab") as f:
        for chunk in response.iter_content(chunk_size=1024 * 100):
            if chunk:
                size = f.write(chunk)
                f.flush()
                bar.update(size)
            else:
                print(response.status_code)
                print(response.text)
                break


def download_file(url: str):
    file_name = url.split('/')[-1]
    file_name = parse.unquote(file_name)
    file_name = f'./file/{file_name}'

    # info = f'downloading {file_name}'
    # p(info)

    content_length = int(requests.get(
        url, auth=(config['webdav']['username'], config['webdav']['password']), stream=True).headers['Content-Length'])

    with tqdm(desc=file_name, total=content_length, unit='B', unit_scale=True, leave=False) as bar:
        if os.path.exists(file_name):
            bar.update(os.path.getsize(file_name))

        while True:
            append_to_log(
                f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {file_name} loop')
            if os.path.exists(file_name):
                temp_size = os.path.getsize(file_name)  # 本地已经下载的文件大小
            else:
                temp_size = 0

            headers = {'Range': 'bytes=%d-' % temp_size}

            try:
                response = requests.get(url, auth=(
                    config['webdav']['username'], config['webdav']['password']), headers=headers, stream=True)
            except Exception:
                continue

            if os.path.exists(file_name):
                # print(f'{os.path.getsize(file_name)} / {content_length}')

                if os.path.getsize(file_name) == content_length:
                    # info = f'downloaded {file_name}'
                    # p(info)
                    return
            try:
                download(file_name, response, bar)
            except FunctionTimedOut as ex:
                # print(ex)
                pass
            except Exception as ex:
                pass


def single():
    for url in tqdm(urls, leave=False):
        download_file(url)


def multi():
    task_pool = ThreadPoolExecutor(max_workers=4)
    tqdm(task_pool.map(download_file, urls), total=len(urls), leave=False)


def main():
    log.register_p_callback(
        lambda string: file.append_all_text('download.log', string+'\n'))
    single()
    # all_task = [task_pool.submit(download_file, (url)) for url in urls]

    # wait(all_task, return_when=ALL_COMPLETED)


if __name__ == '__main__':
    config = yaml.safe_load(file.read_all_text('config.yaml'))
    urls = file.read_all_lines('paths.txt')
    file.create_dir_if_not_exist('file')
    main()
