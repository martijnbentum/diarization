directory$ = "/Users/martijn.bentum/sections_textgrids/"
table_directory$ = "/Users/martijn.bentum/sections_tables/"
appendInfoLine: directory$
wd$ = directory$ + "*.TextGrid"
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
		table_filename$ = replace$ (filename$, ".TextGrid", ".csv",1)
		name$ = replace$ (filename$, ".TextGrid", "", 1)
		appendInfoLine: "table filename " + table_filename$
		Down to Table: "no", 6, "yes", "no"
		Save as tab-separated file: table_directory$ + table_filename$
		selectObject: "TextGrid " + name$
		plusObject: "Table " + name$
		Remove
	endif
endfor
