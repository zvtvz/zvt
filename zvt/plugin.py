# -*- coding: utf-8 -*-
import argparse

from zvt.autocode.generator import gen_plugin_project


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--entity', help='entity name', default='future')
    parser.add_argument('--prefix', help='project prefix', default='zvt')
    parser.add_argument('--dir', help='project directory', default='.')
    parser.add_argument('--providers', help='providers', default=['joinquant'], nargs='+')

    args = parser.parse_args()

    dir_path = args.dir
    entity = args.entity
    providers = args.providers
    prefix = args.prefix
    gen_plugin_project(prefix=prefix, dir_path=dir_path, entity_type=entity, providers=providers)


if __name__ == '__main__':
    # gen_plugin_project(dir_path='../../', entity_type='macro')
    main()
