/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   sim_release.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

static void	check_finished(t_sim *sim, t_coder *coder)
{
	if (coder->compiles_done != sim->config.compiles_required)
		return ;
	sim->full_coders++;
	if (sim->full_coders == sim->config.coders_count)
	{
		sim->stop = 1;
		sim_wake_all(sim);
	}
}

void	release_dongles(t_coder *coder)
{
	t_sim	*sim;
	long	cooldown_until;

	sim = coder->sim;
	pthread_mutex_lock(&sim->lock);
	cooldown_until = now_ms() + sim->config.dongle_cooldown;
	coder->left->in_use = 0;
	coder->right->in_use = 0;
	coder->left->cooldown_until = cooldown_until;
	coder->right->cooldown_until = cooldown_until;
	coder->compiles_done++;
	check_finished(sim, coder);
	sim_wake_all(sim);
	pthread_mutex_unlock(&sim->lock);
}
