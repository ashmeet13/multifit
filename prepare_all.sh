#!/usr/bin/env bash
# Script to download a Wikipedia dump

# Script is partially based on https://github.com/facebookresearch/fastText/blob/master/get-wikimedia.sh
ROOT="data"
echo "Saving data in ""$ROOT"

    languages="hi te ta ml bn ur ne ar"

    # Iterate the string variable using for loop
    for LANG in $languages; do
        echo "Building ${LANG}"

    DUMP_DIR="${ROOT}/wiki_dumps"
    EXTR_DIR="${ROOT}/wiki_extr"
    WIKI_DIR="${ROOT}/wiki"
    EXTR="wikiextractor"
    mkdir -p "${ROOT}"
    mkdir -p "${DUMP_DIR}"
    mkdir -p "${EXTR_DIR}"
    mkdir -p "${WIKI_DIR}"

    DUMP_FILE="${LANG}wiki-latest-pages-articles.xml.bz2"
    DUMP_PATH="${DUMP_DIR}/${DUMP_FILE}"

    if [ ! -f "${DUMP_PATH}" ]; then
    wget -c "https://dumps.wikimedia.org/""${LANG}""wiki/latest/""${DUMP_FILE}""" -P "${DUMP_DIR}"
    else
    echo "${DUMP_PATH} already exists. Skipping download."
    fi

    # Check if directory exists
    if [ ! -d "${EXTR}" ]; then
    git clone https://github.com/attardi/wikiextractor.git
    cd "${EXTR}"
    python3 setup.py install
    cd ..
    fi

    EXTR_PATH="${EXTR_DIR}/${LANG}"
    if [ ! -d "${EXTR_PATH}" ]; then
    python3 wikiextractor/WikiExtractor.py -s --json -o "${EXTR_PATH}" "${DUMP_PATH}" -q
    else
    echo "${EXTR_PATH} already exists. Skipping extraction."
    fi

    python3 -m multifit.datasets.create_wikitext -i "${EXTR_PATH}"  -l "${LANG}" -o "${WIKI_DIR}" -t 13000000
     echo "---------------------------------------------------------------------------------------"
done