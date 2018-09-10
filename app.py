from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import quandl
from bokeh.embed import components
from bokeh.plotting import figure

### ONE TIME ACTIONS

# set quandl credentials and get AAPL data
quandl.ApiConfig.api_key = "A2ZxqULvCzTjy_-W2sSu"
quandl.ApiConfig.api_version = '2015-04-09'

ticker_df = pd.read_csv('ticker_symbols.csv')
ticker_df.set_index('code', inplace = True)

tickers = ['AAPL', 'HD']

###/\ /\ /\ ONE TIME ACTIONS

## common functions

# function for converting objects to pd_datetime
def pddt(obj):
    return pd.to_datetime(obj)

# sparse_mask!
# make an array of Trues and Falses
# with a fixed number of evenly spaced Trues
def sparse_mask(n_orig, n_keep):
    # n_keep and n_orig must be ints!
    
    def divisible(n, w):
        return (n%w == 0)
    
    mask_vals = None
    
    if n_orig < n_keep: # do nothing
        mask_vals = [True]*n_orig
    
    else:
        spacing = n_orig // n_keep
        ix1s = list(range(1, n_keep * spacing + 1))
        
        # mask_val is True only if corresponding
        # ix1 is divisible by spacing
        mask_vals = map(lambda ix1: ix1 % spacing == 0,
                  ix1s)
        mask_vals = list(mask_vals)
        
        # pad with Falses
        mask_vals += [False] * (n_orig - n_keep*spacing)
        
    return np.array(mask_vals)


# Create the main plot
def create_figure(ticker, ticker_df = ticker_df):

	## plot

	# query data
	df = quandl.get("EOD/" + ticker)

	# make col names and index lowercase
	# make index pd_datetime format
	df.columns = map(str.lower, df.columns)
	df.index.name = str.lower(df.index.name)
	df.index = pddt(df.index)

	# keep only some rows from the df
	start_date_str = '1900'
	end_date_str = '2050'
	df_sub = df[(df.index > pddt(start_date_str)) & (df.index < pddt(end_date_str))]
	df_sub = df_sub[['close']]

	# sparsify
	n_points = 40
	df_sub = df_sub.iloc[sparse_mask(len(df_sub), n_points)]

	# diffs
	df_sub['diff'] = df_sub['close'].diff()
	df_sub['close_yest'] = df_sub['close'].shift()
	fall_dates = df_sub.index[df_sub['diff'] < 0]

	# make figure skeleton
	p = figure(x_axis_type="datetime", title = ticker_df['name'][ticker])
	p.yaxis.axis_label = "Price"
	p.xaxis.axis_label = "Date"
	p.xaxis.major_label_orientation = np.pi/4
	p.grid.grid_line_alpha=0.3

	# candlestick width
	width = (df_sub.index[-1] - df_sub.index[0]).total_seconds() / n_points * .7 \
	    * 1000 # candlestick width in ms
	    
	# rises
	rise_dates = df_sub.index[df_sub['diff'] > 0]
	p.vbar(rise_dates, width, df_sub['close_yest'][rise_dates], df_sub['close'][rise_dates], 
	       fill_color="dodgerblue", line_color="white") # rises

	# falls
	fall_dates = df_sub.index[df_sub['diff'] < 0]
	p.vbar(fall_dates, width, df_sub['close_yest'][fall_dates], df_sub['close'][fall_dates], 
	       fill_color="coral", line_color="white") # rises

	return p

# Index page
app = Flask(__name__)
@app.route('/')

def index():

	# Determine the selected feature
	# current_ticker = request.args.get("ticker")
	# if current_ticker == None:
	# 	current_ticker = "AAPL"

	# # Create the plot
	# plot = create_figure(current_ticker)
		
	# # Embed plot into HTML via Flask Render
	# script, div = components(plot)
	# return render_template("template.html", script=script, div=div,
	# 	tickers = tickers,  current_ticker = current_ticker)


	return render_template("template.html")

# With debug=True, Flask server will auto-reload 
# when there are code changes
if __name__ == '__main__':
	app.run(port=5000, debug=True)