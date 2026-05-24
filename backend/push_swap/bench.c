
#include "push_swap.h"

static double	compute_disorder(t_stack *a)
{
	t_stack	*i;
	t_stack	*j;
	int		mistakes;
	int		total_pairs;
	double	res;

	mistakes = 0;
	total_pairs = 0;
	i = a;
	while (i)
	{
		j = i->next;
		while (j)
		{
			total_pairs++;
			if (i->val > j->val)
				mistakes++;
			j = j->next;
		}
		i = i->next;
	}
	if (total_pairs == 0)
		return (0.0);
	res = (double)mistakes / total_pairs;
	return (res);
}

static void	print_disorder(double disorder)
{
	int	p;

	p = disorder * 10000;
	ft_putnbr_fd(p / 100, 2);
	write(2, ".", 1);
	if ((p % 100) < 10)
		write(2, "0", 1);
	ft_putnbr_fd(p % 100, 2);
	write(2, "%\n", 2);
}

void	init_bench(t_bench *bench, t_stack *a, int is_enabled)
{
	bench->benchmark_enabled = is_enabled;
	bench->disorder = compute_disorder(a);
	bench->sa_c = 0;
	bench->sb_c = 0;
	bench->ss_c = 0;
	bench->pa_c = 0;
	bench->pb_c = 0;
	bench->ra_c = 0;
	bench->rb_c = 0;
	bench->rr_c = 0;
	bench->rra_c = 0;
	bench->rrb_c = 0;
	bench->rrr_c = 0;
}

static void	write_nb_ops(t_bench *bench)
{
	ft_putstr_fd("\n[bench] sa:  ", 2);
	ft_putnbr_fd(bench->sa_c, 2);
	ft_putstr_fd("  sb:  ", 2);
	ft_putnbr_fd(bench->sb_c, 2);
	ft_putstr_fd("  ss:  ", 2);
	ft_putnbr_fd(bench->ss_c, 2);
	ft_putstr_fd("  pa:  ", 2);
	ft_putnbr_fd(bench->pa_c, 2);
	ft_putstr_fd("  pb:  ", 2);
	ft_putnbr_fd(bench->pb_c, 2);
	ft_putstr_fd("\n[bench] ra:  ", 2);
	ft_putnbr_fd(bench->ra_c, 2);
	ft_putstr_fd("  rb:  ", 2);
	ft_putnbr_fd(bench->rb_c, 2);
	ft_putstr_fd("  rr:  ", 2);
	ft_putnbr_fd(bench->rr_c, 2);
	ft_putstr_fd("  rra:  ", 2);
	ft_putnbr_fd(bench->rra_c, 2);
	ft_putstr_fd("  rrb:  ", 2);
	ft_putnbr_fd(bench->rrb_c, 2);
	ft_putstr_fd("  rrr:  ", 2);
	ft_putnbr_fd(bench->rrr_c, 2);
	write(2, "\n", 1);
}

void	write_bench(t_bench *bench, t_config *config)
{
	ft_putstr_fd("[bench] disorder:  ", 2);
	print_disorder(bench->disorder);
	ft_putstr_fd("[bench] strategy:  ", 2);
	if (config->algo == ADAPTIVE)
	{
		ft_putstr_fd("Adaptative / ", 2);
		if (bench->disorder < 0.2)
			ft_putstr_fd("O(n2)", 2);
		if (bench->disorder >= 0.2 && bench->disorder < 0.5)
			ft_putstr_fd("O(n√n)", 2);
		if (bench->disorder >= 0.5)
			ft_putstr_fd("O(n log n)", 2);
	}
	if (config->algo == SIMPLE)
		ft_putstr_fd("Simple / O(n2)", 2);
	if (config->algo == MEDIUM)
		ft_putstr_fd("Medium / O(n√n)", 2);
	if (config->algo == COMPLEX)
		ft_putstr_fd("Complex / O(n log n)", 2);
	ft_putstr_fd("\n[bench] total_ops:  ", 2);
	ft_putnbr_fd(bench->sa_c + bench->sb_c + bench->ss_c + bench->pa_c
		+ bench->pb_c + bench->ra_c + bench->rb_c + bench->rr_c + bench->rra_c
		+ bench->rrb_c + bench->rrr_c, 2);
	write_nb_ops(bench);
}
