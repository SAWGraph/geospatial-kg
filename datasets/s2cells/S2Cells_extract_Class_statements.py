input = 'il_s2-l13.ttl'
output = 'il_s2-l13_Class_statements_only.ttl'

with open (output, 'w') as outfile:
    with open(input, 'r') as infile:
        for line in infile:
            if ('@prefix' in line.lower()) or ('s2cell_level13' in line.lower()):
                outfile.write(line.replace(';', '.'))