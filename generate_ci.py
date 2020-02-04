import sys
import os

include_yml = """\
language: generic
matrix:
  include:
"""

before_install_yml = """\
# default phases
before_install:
  - mkdir -p "$HOME/bin"
  - curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR="$HOME/bin" sh
  - export PATH="$PATH:$HOME/bin"
  - arduino-cli core update-index --additional-urls https://downloads.arduino.cc/packages/package_index.json
  - arduino-cli core update-index --additional-urls https://raw.githubusercontent.com/Seeed-Studio/Seeed_Platform/master/package_seeeduino_boards_index.json
  - arduino-cli  core install arduino:avr --additional-urls https://downloads.arduino.cc/packages/package_index.json
  - arduino-cli  core install Seeeduino:samd --additional-urls https://raw.githubusercontent.com/Seeed-Studio/Seeed_Platform/master/package_seeeduino_boards_index.json
  - |
    installLibrary() {
      local -r repositoryFullName="$1"
      local -r repositoryName="${repositoryFullName##*/}"
      # clone repository to the libraries folder of the sketchbook
      git clone https://github.com/${repositoryFullName} "${HOME}/Arduino/libraries/${repositoryName}"
      cd "${HOME}/Arduino/libraries/${repositoryName}"
      cd "${TRAVIS_BUILD_DIR}"
    }
"""
installLibrary_yml = """\
  - buildExampleSketch() { arduino-cli compile  --warnings all --fqbn $BOARD $PWD/examples/$1 --verbose; }
  - buildExampleUtilitySketch() { arduino-cli compile --warnings all --fqbn $BOARD $PWD/examples/utility/$1 --verbose; }
install:
  - mkdir -p $HOME/Arduino/libraries
script:
"""
end_yml = """\
notifications:
  webhooks:
    urls:
      - https://www.travisbuddy.com/
    on_success: never
    on_failure: always\n
"""


#     - env:
#         - BOARD = "arduino:avr:uno"
#     - env:
#         - BOARD = "Seeeduino:samd:seeed_XIAO_m0"


#   - |
#     if [ "$BOARD" == "arduino:avr:uno" ]; then
#       buildExampleSketch Accelerometer_Compass;
#     fi
#   - |
#     if [ "$BOARD" == "Seeeduino:samd:seeed_XIAO_m0" ]; then
#       buildExampleSketch Accelerometer_Compass;
#     fi


def build_yml(board_stings, stretch_strings, repo_strings):
    env_str = "    - env:\n"
    board_str = "        - BOARD = "
    start_str = ""
    end_str = ""

    for board in board_stings:
        start_str = start_str + env_str
        start_str = start_str + board_str + "\""+board + "\"" + "\n"
    print(start_str)

    if stretch_strings != None:
        for board in board_stings:
            for stretch in stretch_strings:
                end_str = end_str + "    - |\n"
                end_str = end_str + \
                    "      if [ \"$BOARD\" == \"" + board + "\" ]; then\n"
                end_str = end_str + "        buildExampleSketch " + stretch + ";\n"
                end_str = end_str + "      fi\n"

        print(end_str)

    mid_str = "  - installLibrary Seeeed-Studio/" + repo_strings+"\n"
    return start_str, mid_str, end_str


def generate_yml(yml_file, boards, not_repos):
    stretchs = []
    # 获取仓库的路径
    repo_path = os.path.abspath(yml_file + "/..")
    # 获取仓库的名字
    repo_name = os.path.abspath(
        yml_file + "/..")[len(os.path.abspath(yml_file + "/../../"))+1:]
    # 查询仓库是否在禁止列表里面
    if True in map(repo_name.endswith, not_repos):
        print("Do nothing")
        return 0
    # 获取所有的Stretch
    stretchs = os.listdir(repo_path+"/examples")
    if not os.path.exists(yml_file):
        # 开始拼装
        start, mid, end = build_yml(boards, stretchs, repo_name)
        ff = open(yml_file, "w")
        yml = include_yml + start + before_install_yml + mid +installLibrary_yml+ end + end_yml
        ff.write(yml)
        ff.close()


if __name__ == "__main__":
    generate_yml("c3.yml", ["arduino:avr:uno",
                            "Seeeduino:samd:seeed_XIAO_m0"], [])
