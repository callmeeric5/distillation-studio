/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   sim_init.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

static int	init_one_dongle(t_sim *sim, int index)
{
	sim->dongles[index].id = index;
	sim->dongles[index].in_use = 0;
	sim->dongles[index].cooldown_until = 0;
	return (heap_init(&sim->dongles[index].waiting,
			sim->config.coders_count, sim));
}

static int	init_dongles(t_sim *sim)
{
	int	i;

	sim->dongles = malloc(sizeof(t_dongle) * sim->config.coders_count);
	if (!sim->dongles)
		return (0);
	memset(sim->dongles, 0, sizeof(t_dongle) * sim->config.coders_count);
	i = 0;
	while (i < sim->config.coders_count)
	{
		if (!init_one_dongle(sim, i))
			return (0);
		i++;
	}
	return (1);
}

static void	fill_coder(t_sim *sim, int index)
{
	int	count;

	count = sim->config.coders_count;
	sim->coders[index].id = index + 1;
	sim->coders[index].compiles_done = 0;
	sim->coders[index].last_compile_start = sim->start_time;
	sim->coders[index].left = &sim->dongles[index];
	if (count == 1)
		sim->coders[index].right = &sim->dongles[index];
	else
		sim->coders[index].right = &sim->dongles[(index + 1) % count];
	sim->coders[index].sim = sim;
}

static int	init_coders(t_sim *sim)
{
	int	i;

	sim->coders = malloc(sizeof(t_coder) * sim->config.coders_count);
	if (!sim->coders)
		return (0);
	memset(sim->coders, 0, sizeof(t_coder) * sim->config.coders_count);
	i = 0;
	while (i < sim->config.coders_count)
	{
		fill_coder(sim, i);
		if (pthread_cond_init(&sim->coders[i].cond, NULL) != 0)
			return (0);
		i++;
	}
	return (1);
}

int	init_sim(t_sim *sim, t_config config)
{
	memset(sim, 0, sizeof(*sim));
	sim->config = config;
	sim->start_time = now_ms();
	if (pthread_mutex_init(&sim->lock, NULL) != 0)
		return (0);
	if (pthread_mutex_init(&sim->log_lock, NULL) != 0)
		return (0);
	if (!init_dongles(sim))
		return (0);
	if (!init_coders(sim))
		return (0);
	return (1);
}
