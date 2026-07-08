/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   codexion.h                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CODEXION_H
# define CODEXION_H

# include <pthread.h>
# include <stdlib.h>
# include <stdio.h>
# include <string.h>
# include <unistd.h>
# include <sys/time.h>
# include <time.h>

typedef enum e_scheduler
{
	CODEX_FIFO,
	CODEX_EDF
}	t_scheduler;

typedef struct s_sim		t_sim;
typedef struct s_coder		t_coder;
typedef struct s_request	t_request;

typedef struct s_config
{
	int			coders_count;
	long		time_to_burnout;
	long		time_to_compile;
	long		time_to_debug;
	long		time_to_refactor;
	int			compiles_required;
	long		dongle_cooldown;
	t_scheduler	scheduler;
}	t_config;

typedef struct s_heap
{
	t_request	**items;
	int			size;
	int			capacity;
	t_sim		*sim;
}	t_heap;

typedef struct s_dongle
{
	int			id;
	int			in_use;
	long		cooldown_until;
	t_heap		waiting;
}	t_dongle;

struct s_request
{
	t_coder		*coder;
	long		sequence;
	long		deadline;
};

struct s_coder
{
	int				id;
	int				compiles_done;
	long			last_compile_start;
	pthread_t		thread;
	pthread_cond_t	cond;
	t_dongle		*left;
	t_dongle		*right;
	t_sim			*sim;
};

struct s_sim
{
	t_config		config;
	t_coder			*coders;
	t_dongle		*dongles;
	pthread_t		monitor;
	pthread_mutex_t	lock;
	pthread_mutex_t	log_lock;
	long			start_time;
	long			next_sequence;
	int				stop;
	int				full_coders;
};

int		parse_args(int argc, char **argv, t_config *config);
int		init_sim(t_sim *sim, t_config config);
int		run_sim(t_sim *sim);
void	destroy_sim(t_sim *sim);

int		heap_init(t_heap *heap, int capacity, t_sim *sim);
void	heap_destroy(t_heap *heap);
int		heap_push(t_heap *heap, t_request *request);
void	heap_remove(t_heap *heap, t_request *request);
int		heap_has(t_heap *heap, t_request *request);
void	heap_peek(t_heap *heap, t_request **request);
void	heap_up(t_heap *heap, int index);
void	heap_down(t_heap *heap, int index);

void	sim_wake_all(t_sim *sim);
void	sim_log_state(t_sim *sim, int id, char *message);
int		sim_is_stopped(t_sim *sim);
void	sim_sleep(t_sim *sim, long ms);
void	sim_set_wait_timeout(struct timespec *time);
int		take_dongles(t_coder *coder);
void	release_dongles(t_coder *coder);
void	*coder_routine(void *data);
void	*monitor_routine(void *data);

long	now_ms(void);
long	sim_time(t_sim *sim);
void	sleep_ms(long ms);

#endif
