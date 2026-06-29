
x_start = 30
x_end = 610
y_start = 30
y_end = 465

width = x_end - x_start
height = y_end - y_start

def get_square_from_coordinates(x, y):
	square_w = width / 8
	square_h = height / 8    

	col_idx = int((x - x_start) // square_w)
	row_idx = int((y - y_start) // square_h)

	col_idx = max(0, min(7, col_idx))
	row_idx = int(max(0, min(7, row_idx)))
    

	files = ['h','g','f','e','d','c','b','a']
	ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
    
	return f"{files[col_idx]}{ranks[row_idx]}"

