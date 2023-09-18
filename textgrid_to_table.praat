directory$ = "/Users/martijn.bentum/sections_textgrids/"
table_directory$ = "/Users/martijn.bentum/sections_tables/"
writeInfoLine: directory$
wd$ = directory$ + "*.textgrid"
file_list = Create Strings as file list: "file_list", wd$

selectObject: file_list

number_of_files = Get number of strings
for i from 1 to number_of_files
	appendInfoLine: i
	selectObject: file_list
	filename$ = Get string: i
	appendInfoLine: filename$
	Read from file: directory$ + filename$
	if not fileReadable(directory$ + filename$)
		appendInfoLine: "file not readable" + " " + directory$ + filename$
	else
		appendInfoLine: "file readable " + filename$
		table_filename$ = replace$ (filename$, ".textgrid", ".table",1)
		name$ = replace$ (filename$, ".textgrid", "", 1)
		appendInfoLine: "table filename " + table_filename$
		Down to Table: "no", 3, "yes", "no"
		Save as tab-separated file: table_directory$ + table_filename$
		selectObject: "TextGrid " + name$
		plusObject: "Table " + name$
		Remove
	endif
endfor
