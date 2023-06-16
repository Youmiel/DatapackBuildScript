import os
import re
import time
from typing import Any, List, Union
import shutil

from mako.template import Template
from mako.lookup import TemplateLookup


def scan_folder(path: str, max_recursion: int = 15, file_ext='.*', file_regex: str = '.*', log: bool = True) -> list[str]:
    pattern_ext = re.compile(file_ext)
    pattern_file = re.compile(file_regex)
    result = []
    sub_path = os.listdir(path)
    if log:
        print('Scanning', path, '...', len(sub_path), 'files/directories')
    for sub in sub_path:
        full_path = os.path.join(path, sub)
        if os.path.isfile(full_path) and \
                re.match(pattern_ext, os.path.splitext(sub)[1]) is not None and \
                re.match(pattern_file, sub) is not None:
            result.append(full_path)
        elif max_recursion != 0 and os.path.isdir(full_path):
            result.extend(scan_folder(
                full_path, max_recursion-1, file_ext, file_regex, log))
    return result


def print_progress_bar(current_value, max_value, start_time, bar_length: int = 10, back_length: int = 0):
    progress = current_value / max_value
    estimate_time = (time.time() - start_time) / progress * \
        (1 - progress) if progress > 0 else -60
    bar_count = round(progress * bar_length)

    print_string = "({} / {}) {} [{:.1f} % / 100 %] (eta {:.1f} min)".format(
        current_value, max_value, '|' * bar_count + '-' * (bar_length - bar_count), current_value / max_value * 100, estimate_time / 60)
    print('\b' * back_length, end='', flush=True)
    print(print_string, end='', flush=True)

    return len(print_string)


def get_new_name(original_path, index, is_directory: bool = False) -> str:
    if not is_directory:
        root, ext = os.path.splitext(original_path)
        return root + '_{}'.format(index) + ext
    else:
        return original_path + '_{}'.format(index)


def check_before_create(path: str, is_directory: bool = False, overwrite: bool = False) -> str:
    actual_path = path
    if os.path.exists(path):
        rename = 1
        if overwrite:
            while True:
                if is_directory and os.path.isdir(actual_path):
                    break
                elif not is_directory and os.path.isfile(actual_path):
                    break
                else:
                    actual_path = get_new_name(path, rename, is_directory)
                    rename += 1
            return actual_path
        else:
            while os.path.exists(actual_path):
                actual_path = get_new_name(path, rename, is_directory)
                rename += 1
            return actual_path
    else:
        if is_directory:
            mkdir_name = path
        else:
            mkdir_name = os.path.dirname(path)
        os.makedirs(mkdir_name, exist_ok=True)
        return path


def check_and_write_file(path: str, content: Union[str, bytes], overwrite: bool = False):
    actual_path = check_before_create(path, False, overwrite)

    if type(content) is bytes:
        with open(actual_path, 'bw') as bin_file:
            bin_file.write(content)
    elif type(content) is str:
        with open(actual_path, 'w', encoding='utf-8') as file:
            file.write(content)
    else:
        print('Unknown content.')


TEMPLATE_DIR = 'src/'
TARGET_DIR = 'data/'
MAKO_EXT = '.mako'
MAKO_HEADER = '.hamko'


def run(template_dir: str = TEMPLATE_DIR, target_dir: str = TARGET_DIR):
    shutil.rmtree(TARGET_DIR, ignore_errors=False)
    template_path_list = scan_folder(TEMPLATE_DIR, log=False)

    template_lookup = TemplateLookup(directories=["./"])
    for template_file in template_path_list:
        filename, ext = os.path.splitext(os.path.basename(template_file))
        if ext == MAKO_EXT:
            real_filename = filename
            relative_dir = os.path.relpath(
                os.path.dirname(template_file), start=TEMPLATE_DIR)
            target_file = os.path.join(TARGET_DIR, relative_dir, real_filename)

            template = Template(filename=template_file, lookup=template_lookup)
            content = template.render()

            check_and_write_file(target_file, content, overwrite=True)
        elif ext == MAKO_HEADER:
            pass
        else:
            real_filename = os.path.basename(template_file)
            relative_dir = os.path.relpath(
                os.path.dirname(template_file), start=TEMPLATE_DIR)
            target_file = os.path.join(TARGET_DIR, relative_dir, real_filename)

            check_before_create(
                target_file, is_directory=False, overwrite=True)
            shutil.copyfile(template_file, target_file)

    print("BUILD SUCCESS")


if __name__ == '__main__':
    run()
