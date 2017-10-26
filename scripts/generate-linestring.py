import sys
from alti.tests.integration.test_profile import create_line


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.exit(1)
    nb_pts = int(sys.argv[1])
    with open('payload.json', 'w+') as f:
        f.write(create_line(nb_pts))


if __name__ == '__main__':
    main()
