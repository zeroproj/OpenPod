/*
 * Flutter: guide a puffball through gaps between crystal pillars.
 * Center flaps, Back twice exits.  Runs as a full-screen overlay opened
 * from the Applications menu.
 *
 * Positions and speeds are fixed point with 4 fractional bits; the
 * simulation runs in fixed 33 ms steps driven by an LVGL timer, catching
 * up if the timer fires late.
 *
 * Based on the SL6801_player SDK by Dmitry Brant, used with permission.
 */
#include "bird_dazed.h"
#include "bird_down.h"
#include "bird_up.h"
#include "sdk.h"

#define FP 16
#define STEP_MS 33
#define MAX_STEPS 4

#define GROUND_H 14
#define BIRD_X 28
#define BIRD_W 16
#define BIRD_H 12
#define HIT_INSET 2

#define PIPES 3
#define PIPE_W 18
#define PIPE_SPACING 68
#define CAP_H 5
#define CAP_OVERHANG 2
#define GAP_START 56
#define GAP_MIN 44

#define SPEED (FP * 3 / 2)
#define GRAVITY 5
#define FLAP_V (-58)
#define MAX_FALL 72
#define FLAP_FRAMES 5
#define RETRY_DELAY_MS 700
#define BACK_EXIT_MS 800

#define COLOR_SKY lv_rgb(0x1E, 0x2A, 0x55)
#define COLOR_STAR lv_rgb(0xC8, 0xD0, 0xF0)
#define COLOR_MOON lv_rgb(0xF4, 0xEC, 0xC8)
#define COLOR_PILLAR lv_rgb(0x22, 0xA8, 0x9A)
#define COLOR_PILLAR_EDGE lv_rgb(0x0E, 0x55, 0x4E)
#define COLOR_CAP lv_rgb(0x8C, 0xF0, 0xE0)
#define COLOR_GRASS lv_rgb(0x3C, 0x9A, 0x3C)
#define COLOR_SOIL lv_rgb(0x5A, 0x3E, 0x24)
#define COLOR_TEXT lv_rgb(0xFF, 0xFF, 0xFF)
#define COLOR_TITLE lv_rgb(0xFF, 0xD2, 0x4A)

enum { READY, PLAYING, DEAD };

typedef struct {
	lv_obj_t *top, *top_cap, *bot, *bot_cap;
	int32_t x;
	lv_coord_t gap_y, gap;
	bool scored;
} pillar_t;

typedef struct {
	fw_overlay_t *ov;
	lv_timer_t *timer;
	lv_obj_t *bird, *score_label, *title, *hint;
	const lv_img_dsc_t *bird_src;
	pillar_t pillar[PIPES];
	lv_coord_t w, ground_y;
	int32_t y, v;
	uint32_t last_tick, acc, rng;
	uint32_t frame, flap_frame, dead_ms;
	uint32_t last_back;
	uint16_t score, best;
	uint8_t state;
	bool press_handled;
} game_t;

static uint32_t rnd(game_t *g)
{
	uint32_t x = g->rng;
	x ^= x << 13;
	x ^= x >> 17;
	x ^= x << 5;
	return g->rng = x;
}

static void set_bird_src(game_t *g, const lv_img_dsc_t *src)
{
	if (g->bird_src != src) {
		g->bird_src = src;
		lv_img_set_src(g->bird, src);
	}
}

static void set_score_text(game_t *g)
{
	char buf[8];
	fw_put_dec(buf, g->score);
	lv_label_set_text(g->score_label, buf);
}

static void layout_pillar_sizes(game_t *g, pillar_t *p)
{
	lv_coord_t bot_y = p->gap_y + p->gap;
	lv_obj_set_size(p->top, PIPE_W, p->gap_y);
	lv_obj_set_size(p->bot, PIPE_W, g->ground_y - bot_y);
}

static void place_pillar(game_t *g, pillar_t *p)
{
	lv_coord_t x = (lv_coord_t)(p->x / FP);
	lv_coord_t bot_y = p->gap_y + p->gap;
	lv_obj_set_pos(p->top, x, 0);
	lv_obj_set_pos(p->top_cap, x - CAP_OVERHANG, p->gap_y - CAP_H);
	lv_obj_set_pos(p->bot, x, bot_y);
	lv_obj_set_pos(p->bot_cap, x - CAP_OVERHANG, bot_y);
	(void)g;
}

static void new_gap(game_t *g, pillar_t *p)
{
	int shrink = g->score / 4 * 2;
	p->gap = (lv_coord_t)(GAP_START - shrink < GAP_MIN ? GAP_MIN : GAP_START - shrink);
	lv_coord_t lo = 12 + CAP_H, hi = g->ground_y - p->gap - 12 - CAP_H;
	p->gap_y = (lv_coord_t)(lo + (lv_coord_t)(rnd(g) % (uint32_t)(hi - lo + 1)));
	p->scored = false;
	layout_pillar_sizes(g, p);
}

static void show_message(game_t *g, const char *title, const char *hint)
{
	lv_label_set_text(g->title, title);
	lv_label_set_text(g->hint, hint);
	lv_obj_align(g->title, LV_ALIGN_TOP_MID, 0, 34);
	lv_obj_align(g->hint, LV_ALIGN_TOP_MID, 0, 52);
	lv_obj_clear_flag(g->title, LV_OBJ_FLAG_HIDDEN);
	lv_obj_clear_flag(g->hint, LV_OBJ_FLAG_HIDDEN);
}

static void hide_message(game_t *g)
{
	lv_obj_add_flag(g->title, LV_OBJ_FLAG_HIDDEN);
	lv_obj_add_flag(g->hint, LV_OBJ_FLAG_HIDDEN);
}

static void reset(game_t *g)
{
	g->state = READY;
	g->score = 0;
	g->y = (g->ground_y / 2 - BIRD_H / 2) * FP;
	g->v = 0;
	g->rng ^= lv_tick_get();
	g->last_back = 0;
	for (int i = 0; i < PIPES; i++) {
		pillar_t *p = &g->pillar[i];
		p->x = (g->w + 24 + i * PIPE_SPACING) * FP;
		new_gap(g, p);
		place_pillar(g, p);
	}
	set_bird_src(g, &img_bird_down);
	lv_obj_set_pos(g->bird, BIRD_X, (lv_coord_t)(g->y / FP));
	set_score_text(g);
	show_message(g, "Flutter", "Center: flap\nBack twice: exit");
}

static void flap(game_t *g)
{
	g->v = FLAP_V;
	g->flap_frame = g->frame;
	set_bird_src(g, &img_bird_up);
}

static void on_center(game_t *g)
{
	switch (g->state) {
	case READY:
		hide_message(g);
		g->state = PLAYING;
		flap(g);
		break;
	case PLAYING:
		flap(g);
		break;
	case DEAD:
		if (g->dead_ms >= RETRY_DELAY_MS)
			reset(g);
		break;
	}
}

static bool overlaps(lv_coord_t ax, lv_coord_t ay, lv_coord_t aw, lv_coord_t ah, lv_coord_t bx, lv_coord_t by,
		     lv_coord_t bw, lv_coord_t bh)
{
	return ax < bx + bw && bx < ax + aw && ay < by + bh && by < ay + ah;
}

static void die(game_t *g)
{
	g->state = DEAD;
	g->dead_ms = 0;
	if (g->score > g->best)
		g->best = g->score;
	set_bird_src(g, &img_bird_dazed);
	char buf[48];
	char *p = fw_put_str(buf, "Score ");
	p = fw_put_dec(p, g->score);
	p = fw_put_str(p, "  Best ");
	p = fw_put_dec(p, g->best);
	fw_put_str(p, "\nCenter: again");
	show_message(g, "Ouch!", buf);
}

static void step(game_t *g)
{
	g->frame++;
	lv_coord_t floor_y = g->ground_y - BIRD_H;

	if (g->state == READY) {
		int phase = (int)(g->frame % 32);
		int off = phase < 16 ? phase : 32 - phase;
		g->y = (g->ground_y / 2 - BIRD_H / 2 - 4 + off / 2) * FP;
		set_bird_src(g, (g->frame / 6) % 2 ? &img_bird_up : &img_bird_down);
		return;
	}

	g->v += GRAVITY;
	if (g->v > MAX_FALL)
		g->v = MAX_FALL;
	g->y += g->v;
	if (g->y < 0) {
		g->y = 0;
		g->v = 0;
	}

	if (g->state == DEAD) {
		g->dead_ms += STEP_MS;
		if (g->y > floor_y * FP)
			g->y = floor_y * FP;
		return;
	}

	if (g->frame - g->flap_frame > FLAP_FRAMES)
		set_bird_src(g, &img_bird_down);

	lv_coord_t by = (lv_coord_t)(g->y / FP);
	for (int i = 0; i < PIPES; i++) {
		pillar_t *p = &g->pillar[i];
		p->x -= SPEED;
		if (p->x < -(PIPE_W + CAP_OVERHANG) * FP) {
			p->x += PIPES * PIPE_SPACING * FP;
			new_gap(g, p);
		}
		lv_coord_t px = (lv_coord_t)(p->x / FP);
		if (!p->scored && px + PIPE_W < BIRD_X) {
			p->scored = true;
			g->score++;
			set_score_text(g);
		}
		lv_coord_t hx = BIRD_X + HIT_INSET, hy = by + HIT_INSET;
		lv_coord_t hw = BIRD_W - 2 * HIT_INSET, hh = BIRD_H - 2 * HIT_INSET;
		if (overlaps(hx, hy, hw, hh, px - CAP_OVERHANG, 0, PIPE_W + 2 * CAP_OVERHANG, p->gap_y) ||
		    overlaps(hx, hy, hw, hh, px - CAP_OVERHANG, p->gap_y + p->gap, PIPE_W + 2 * CAP_OVERHANG,
			     g->ground_y - p->gap_y - p->gap)) {
			die(g);
			return;
		}
	}
	if (by >= floor_y) {
		g->y = floor_y * FP;
		die(g);
	}
}

static void render(game_t *g)
{
	lv_obj_set_pos(g->bird, BIRD_X, (lv_coord_t)(g->y / FP));
	if (g->state == PLAYING)
		for (int i = 0; i < PIPES; i++)
			place_pillar(g, &g->pillar[i]);
}

static void tick_cb(lv_timer_t *t)
{
	game_t *g = t->user_data;
	uint32_t now = lv_tick_get();
	g->acc += now - g->last_tick;
	g->last_tick = now;
	int n = 0;
	while (g->acc >= STEP_MS && n < MAX_STEPS) {
		g->acc -= STEP_MS;
		step(g);
		n++;
	}
	if (n == MAX_STEPS)
		g->acc = 0;
	if (n)
		render(g);
}

static void input_cb(lv_event_t *e)
{
	game_t *g = lv_event_get_user_data(e);
	uint8_t code = lv_event_get_code(e);
	if (code == LV_EVENT_PRESSED) {
		g->press_handled = true;
		on_center(g);
		return;
	}
	if (code != LV_EVENT_KEY)
		return;
	uint32_t key = *(uint32_t *)lv_event_get_param(e);
	if (key == FW_KEY_BACK) {
		uint32_t now = lv_tick_get();
		if (g->last_back && now - g->last_back < BACK_EXIT_MS) {
			fw_overlay_close(g->ov); /* frees g via on_delete */
			return;
		}
		g->last_back = now;
		return;
	}
	if (key == FW_KEY_CENTER) {
		if (g->press_handled)
			g->press_handled = false;
		else
			on_center(g);
	}
}

static void on_delete(void *ctx)
{
	game_t *g = ctx;
	if (g->timer)
		lv_timer_del(g->timer);
	lv_mem_free(g);
}

static void build_scene(game_t *g, lv_obj_t *root, lv_coord_t h)
{
	static const uint8_t stars[][2] = {{10, 14}, {34, 30}, {58, 8}, {76, 40}, {112, 52}, {20, 70}, {96, 86}, {50, 98}};
	for (unsigned i = 0; i < sizeof(stars) / sizeof(stars[0]); i++)
		lv_obj_set_pos(fw_rect(root, 2, 2, COLOR_STAR), stars[i][0], stars[i][1]);
	lv_obj_t *moon = fw_rect(root, 18, 18, COLOR_MOON);
	lv_obj_set_style_radius(moon, 0x7FFF, 0);
	lv_obj_set_pos(moon, g->w - 30, 10);

	for (int i = 0; i < PIPES; i++) {
		pillar_t *p = &g->pillar[i];
		p->top = fw_rect(root, PIPE_W, 10, COLOR_PILLAR);
		p->bot = fw_rect(root, PIPE_W, 10, COLOR_PILLAR);
		p->top_cap = fw_rect(root, PIPE_W + 2 * CAP_OVERHANG, CAP_H, COLOR_CAP);
		p->bot_cap = fw_rect(root, PIPE_W + 2 * CAP_OVERHANG, CAP_H, COLOR_CAP);
		lv_obj_t *parts[] = {p->top, p->bot, p->top_cap, p->bot_cap};
		for (int k = 0; k < 4; k++) {
			lv_obj_set_style_border_width(parts[k], 1, 0);
			lv_obj_set_style_border_color(parts[k], COLOR_PILLAR_EDGE, 0);
		}
	}

	lv_obj_set_pos(fw_rect(root, g->w, GROUND_H, COLOR_SOIL), 0, g->ground_y);
	lv_obj_set_pos(fw_rect(root, g->w, 2, COLOR_GRASS), 0, g->ground_y);

	g->bird = lv_img_create(root);
	g->bird_src = NULL;

	g->score_label = lv_label_create(root);
	lv_obj_set_style_text_color(g->score_label, COLOR_TEXT, 0);
	lv_obj_set_style_text_align(g->score_label, LV_TEXT_ALIGN_CENTER, 0);
	lv_obj_set_width(g->score_label, g->w);
	lv_obj_set_pos(g->score_label, 0, 4);

	g->title = fw_label(root, "", COLOR_TITLE);
	g->hint = fw_label(root, "", COLOR_TEXT);
	lv_obj_set_style_text_align(g->hint, LV_TEXT_ALIGN_CENTER, 0);
	(void)h;
}

void flutter_open(lv_obj_t *return_focus)
{
	game_t *g = lv_mem_alloc(sizeof(game_t));
	if (!g)
		return;
	memset(g, 0, sizeof(*g));
	g->rng = FW_SYSTICK_VAL ^ 0x9E3779B9u;
	if (!g->rng)
		g->rng = 1;
	g->ov = fw_overlay_open(return_focus, COLOR_SKY, on_delete, g);
	if (!g->ov) {
		lv_mem_free(g);
		return;
	}
	lv_obj_t *root = g->ov->root;
	lv_coord_t h = lv_disp_get_ver_res(NULL);
	g->w = lv_disp_get_hor_res(NULL);
	g->ground_y = h - GROUND_H;

	build_scene(g, root, h);
	reset(g);

	lv_obj_add_event_cb(root, input_cb, LV_EVENT_PRESSED, g);
	lv_obj_add_event_cb(root, input_cb, LV_EVENT_KEY, g);
	g->last_tick = lv_tick_get();
	g->timer = lv_timer_create(tick_cb, STEP_MS / 2, g);
}
