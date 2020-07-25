#!/bin/bash
pandoc -o out/SCP\ Series.epub metadata.txt series-1/*.md --css style.css --table-of-contents;
kindlegen out/SCP\ Series.epub;

