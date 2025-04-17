#! /usr/bin/ruby

require 'matlab'
require 'excel'
require 'trollop'

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
matout     Monte Carlo outputs (.mat format).

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

# Fill colors
def getFillColor( direction, value, yellowLimit, redLimit )
	
	color = {:green => '99ff99', :yellow => 'ffff99', :red => 'ff99cc', :grey => 'f2f2f2' }
	
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
    end
    
    # Start engine
    eng = Matlab::Engine.new
    eng.stealthEval("addpath('#{opts[:path]}')")

    # Open template
    wb = Excel::XLSX.new
    wb.open(opts[:template])

    # For each matout
    ARGV.each_with_index do | matout, index |

        # Load matout
        eng.stealthEval('clear')
        eng.load(matout)
        eng.stealthEval('ans = 0;')

        # Cell Block
        wb.cellBlock(keyHead, headers) do |cell, results|

            out = Hash[symbols.zip results]

            if /ans\s*=/.match(out[:calculation]) && out[:type]

        		eng.stealthEval('ans = 0;')
				eng.stealthEval(out[:calculation]+';')

                evalString = getEvalString(out[:type])
                value = eng.scalarEval( evalString )
                color = getFillColor(out[:direction], value, out[:yellow], out[:red])
            
                cell.raw_value = value
                cell.change_fill color

                puts "#{cell.worksheet.sheet_name}: #{out[:type]} #{out[:metric]} = #{value} (#{out[:units]})" if opts[:verbose]
            end
        end
        
    end

    # Save and close
    wb.save('ScoreCardResults.xlsx')
    eng.close

end

