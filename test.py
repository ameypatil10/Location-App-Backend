def var_new(num_old, num, x, avg_old, var_old):
	var = num_old*(var_old + (((x-avg_old)**2)/num) )/num
	return var