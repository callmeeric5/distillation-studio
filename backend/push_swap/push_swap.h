/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   push_swap.h                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ziwang <ziwang@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/04/27 12:53:21 by ziwang            #+#    #+#             */
/*   Updated: 2026/05/05 17:03:47 by ziwang           ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef PUSH_SWAP_H
# define PUSH_SWAP_H

# include <stdlib.h>
# include <unistd.h>
# define INT_MAX 2147483647
# define INT_MIN -2147483648

typedef struct s_stack
{
	int				val;
	int				index;
	struct s_stack	*next;
	struct s_stack	*prev;
}					t_stack;

typedef struct s_move
{
	int				cost_a;
	int				cost_b;
	int				total;
	t_stack			*target;
}					t_move;

typedef struct s_sizes
{
	int				a;
	int				b;
}					t_sizes;

typedef struct s_bench
{
	int				benchmark_enabled;
	double			disorder;
	int				sa_c;
	int				sb_c;
	int				ss_c;
	int				pa_c;
	int				pb_c;
	int				ra_c;
	int				rb_c;
	int				rr_c;
	int				rra_c;
	int				rrb_c;
	int				rrr_c;
}					t_bench;

typedef struct s_rot_fns
{
	void			(*up)(t_stack **, t_bench *);
	void			(*down)(t_stack **, t_bench *);
}					t_rot_fns;

typedef enum e_algo_type
{
	NONE,
	ADAPTIVE,
	SIMPLE,
	MEDIUM,
	COMPLEX
}					t_algo_type;

typedef struct s_config
{
	t_algo_type		algo;
	int				mode;
}					t_config;

void				swap(t_stack **stack);
void				push(t_stack **src, t_stack **dst);
void				rotate(t_stack **stack);
void				reverse_rotate(t_stack **stack);
void				sa(t_stack **a, t_bench *bench);
void				pa(t_stack **b, t_stack **a, t_bench *bench);
void				ra(t_stack **a, t_bench *bench);
void				rra(t_stack **a, t_bench *bench);
void				sb(t_stack **b, t_bench *bench);
void				pb(t_stack **a, t_stack **b, t_bench *bench);
void				rb(t_stack **b, t_bench *bench);
void				rrb(t_stack **b, t_bench *bench);
void				ss(t_stack **a, t_stack **b, t_bench *bench);
void				rr(t_stack **a, t_stack **b, t_bench *bench);
void				rrr(t_stack **a, t_stack **b, t_bench *bench);
void				quick_sort(int *arr, int low, int high);
size_t				get_stack_size(t_stack *stack);
int					is_sorted_stack(t_stack *stack);
void				display_stack_error(t_stack **a);
void				push_stack(t_stack **stack, int val);
void				clear_stack(t_stack **stack);
void				init_stack_idx(t_stack **stack);
int					ft_strcmp(char *dst, char *src);
t_algo_type			extract_strategy(char *str);
void				validate(char **argv, t_stack **stack, t_config *config);
int					extract_number(char **str, t_stack **stack);
void				init_bench(t_bench *bench, t_stack *a, int is_enabled);
void				ft_putstr_fd(char *s, int fd);
void				ft_putnbr_fd(int n, int fd);
void				write_bench(t_bench *bench, t_config *config);
void				tiny_sort(t_stack **a, t_stack **b, t_bench *bench,
						int size);
void				run_sort(t_stack **a, t_stack **b, t_bench *bench,
						t_config *config);

int					get_min_pos(t_stack *stack);
void				simple_sort(t_stack **a, t_stack **b, t_bench *bench,
						int size);

void				medium_sort(t_stack **a, t_stack **b, t_bench *bench);
void				complex_sort(t_stack **a, t_stack **b, t_bench *bench,
						int size);
void				adaptive_sort(t_stack **a, t_stack **b, t_bench *bench,
						int size);
t_move				best_move(t_stack *a, t_stack *b);
void				apply_move(t_stack **a, t_stack **b, t_move *m,
						t_bench *bench);
void				move_to_a(t_stack **a, t_stack **b, t_bench *bench);
void				rotate_both(t_stack **a, t_stack **b, t_move *m,
						t_bench *bench);
void				rotate_steps(t_stack **stack, int *steps, t_bench *bench,
						t_rot_fns fns);
void				final_align(t_stack **a, t_bench *bench);
void				calc_move(t_move *m, t_stack *a, t_stack *b, t_stack *n);
int					get_target_pos(t_stack *a, int b_idx);
int					pos_in_stack(t_stack *stack, t_stack *node);
int					*set_chunks(t_stack **a, int nb_chunks);

void				push_chunk_to_b(t_stack **a, t_stack **b, int max,
						t_bench *bench);
void				push_all_b_to_a(t_stack **a, t_stack **b, t_bench *bench);
int					get_min_val_stack(t_stack *stack);
void				ft_sort_int_tab(int *tab, int size);
int					*stack_to_array(t_stack *a);
void				fill_tab_chunks(int *chunks_tab, int nb_chunks,
						int size_stack, int *arr);
int					get_val_pos_stack(t_stack *stack, int val);
t_stack				*last_node(t_stack *stack);
int					get_max_val_stack(t_stack *stack);
int					find_target_in_b(t_stack *stack, int val);
int					get_max_val_stack(t_stack *stack);
void				sort_two(t_stack **a, t_bench *bench);
#endif
