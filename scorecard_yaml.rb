#! /usr/bin/ruby

require 'matlab'
require 'excel'
require 'trollop'
require 'yaml'

scriptName = File.basename(__FILE__)
# ------------------------
#  Help message banner
# ------------------------
myBanner = <<-BANNER
#{scriptName} (c) 2018 David Way
Monte Carlo outputs scorecard.

Usage:
#{scriptName} [options] matout

Arguments:
moutout     Monte Carlo outputs (.mat format).

Options:
BANNER
# ----- end banner -------


# Column headers
keyHead = 'POST Results'
headers = ['Metric','Type','Units','Calculation', '<,>', 'Flag', 'Out of Spec']
symbols = [:metric, :type, :units, :calculation,  :direction, :yellow, :red]

# Evaluation types
def getEvalString( type )
	return case type
		when /^(.+)%-tile/i then "prctile(ans,#{$1})"
		when /mean/i 		then "mean(ans)"
		when /var/i 		then "var(ans)"
		when /std/i 		then "std(ans)"
		when /min/i 		then "min(ans)"
		when /max/i 		then "max(ans)"
		when /size/i 		then "length(ans)"
		when /% of cases/i 	then "percent(ans)"
		when /how many/i 	then "howmany(ans)"
		when /scalar/i 		then "ans"
		else nil
	end
end

# Global Colors
$color = {:green => '99ff99', :yellow => 'ffff99', :red => 'ff99cc', :grey => 'f2f2f2' }
$codes = $color.invert

# Fill colors
def getFillColor( direction, value, yellowLimit, redLimit )
		
	color = $color # local copy
	
	return color[:grey] unless direction!=nil && ( redLimit!=nil || yellowLimit!=nil )
	
    inf = case direction
        when '<'  then  Float::INFINITY
        when '<=' then  Float::INFINITY
        when '>'  then -Float::INFINITY
        when '>=' then -Float::INFINITY
    end

    red = redLimit ? redLimit.to_f : inf
	yellow = yellowLimit ? yellowLimit.to_f : red
	
	case direction.gsub(/\s+/,"")
		when '<'
			return color[:green]  	if value <  yellow
			return color[:yellow] 	if value >= yellow && value < red
			return color[:red]		if value >= red
		when '>'
			return color[:green]  	if value >  yellow
			return color[:yellow] 	if value <= yellow && value > red
			return color[:red]		if value <= red
		when '<='
			return color[:green]  	if value <= yellow
			return color[:yellow] 	if value >  yellow && value <= red
			return color[:red]		if value >  red
		when '>='
			return color[:green]  	if value >= yellow
			return color[:yellow] 	if value <  yellow && value >= red
			return color[:red]		if value <  red
		else
            # puts "Invalid direction: '#{direction}', returning grey color"
            return color[:grey]
	end
end



#**************************
#**************************
if __FILE__ == $0
    
    # Handle command line options and arguments using Trollop:
    opts = Trollop::options do
        
        version "#{scriptName} 1.0 (c) 2018 David Way"
        banner myBanner
        opt :template,	"Scorecard template (.xlsx format).",           :default => 'ScoreCardTemplate.xlsx'
        opt :output,	"Scorecard output filename (.xlsx format).",    :default => 'ScoreCardResults.xlsx'
        opt :path,      "Optional m-file search path.",                 :default => ENV['MATLAB_PATH']
        opt :verbose,   "Verbose output."
        opt :yaml,   	"Dump YAML output instead (results in scorecard.yml)."
    end
    
    # Start engine
    eng = Matlab::Engine.new
    eng.eval("addpath('#{opts[:path]}')")

    # Open template
    wb = Excel::XLSX.new
    wb.open(opts[:template])
	
	# YAML output array
	yaml = Array.new

    # For each matout
    ARGV.each_with_index do | matout, index |

        # Load matout
        eng.eval('clear')
        eng.load(matout)
        eng.eval('ans = 0;')

        # Cell Block
        wb.cellBlock(keyHead, headers) do |cell, results|

            out = Hash[symbols.zip results]

            next unless cell
            next unless /ans\s*/.match(out[:calculation])

            eng.eval(out[:calculation]+';')

            out[:evalString] = getEvalString(out[:type]) or next
            
            out[:value] = eng.scalarEval( out[:evalString] )
            out[:color] = getFillColor(out[:direction], out[:value], out[:yellow], out[:red])
			out[:code]  = $codes[out[:color]]
            
			if opts[:yaml] 
				yaml.push out
			else
				cell.raw_value = out[:value]
            	cell.change_fill out[:color]
			end

            puts "#{cell.worksheet.sheet_name}: #{out[:type]} #{out[:metric]} = #{out[:value]} (#{out[:units]})" if opts[:verbose]
        end
        
    end

    # Save and close
    if opts[:yaml]
		File.open('scorecard.yml','w+') { |file| file.write YAML::dump(yaml) }
	else
		wb.save(opts[:template])
    end
	eng.close

end

