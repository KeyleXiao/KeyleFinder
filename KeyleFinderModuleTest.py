import json
from KeyleFinderModule import KeyleFinderModule


def main():
    big_image = 'demo/layer.png'
    sub_image = 'demo/middle.png'
    finder = KeyleFinderModule(big_image)
    result = finder.locate(sub_image, debug=False)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
