/*
 * Cobrinha (Snake): full-screen 128x160 game.  A 16x18 field of 8 px cells
 * sits below a 16 px score strip.  Prev/Next turn the snake left/right
 * relative to its own direction, Play pauses and resumes (and restarts
 * after game over), Back twice exits.  The GN-438 has no Up/Down key.
 *
 * The field is a 4-bit indexed image in an LVGL heap buffer, drawn in place
 * like Mp3tris; one object per cell would not fit in the 40 KB heap.  The
 * buffer and the timer are freed in LV_EVENT_DELETE.  No writable globals,
 * no sound.
 *
 * Based on the SL6801_player SDK by Dmitry Brant, used with permission.
 */
#include "sdk.h"

#define CELL 8
#define COLS 16
#define ROWS 18
#define FIELD_W (COLS * CELL)
#define FIELD_H (ROWS * CELL)
#define HUD_H 16
#define MAX_CELLS (COLS * ROWS)
#define PALETTE_SIZE (16 * 4)
#define IMG_SIZE (PALETTE_SIZE + FIELD_W / 2 * FIELD_H)

#define START_LEN 3
#define START_MS 220
#define SPEED_STEP_MS 8
#define MIN_MS 70
#define TICK_MS 20
#define MAX_DT 100
#define RETRY_DELAY_MS 700
#define BACK_EXIT_MS 800

#define C_BG 0
#define C_SNAKE 1
#define C_FOOD 2
#define C_HEAD 3

#define COLOR_SNAKE lv_rgb(120, 220, 120)
#define COLOR_FOOD lv_rgb(255, 82, 82)
#define COLOR_HEAD lv_rgb(160, 255, 160)
#define COLOR_TEXT lv_rgb(255, 255, 255)

enum { READY, PLAYING, PAUSED, OVER };

typedef struct {
	uint8_t x, y;
} cell_t;

typedef struct {
	fw_overlay_t *ov;
	lv_timer_t *timer;
	lv_obj_t *img, *score_label, *msg, *msg_title, *msg_text;
	lv_img_dsc_t dsc;
	uint8_t px[IMG_SIZE];
	cell_t body[MAX_CELLS];

	uint16_t len;
	uint8_t dir, next_dir, food_x, food_y;
	uint8_t state;
	uint32_t rng, last_tick, acc, speed_ms, score, last_back, state_ms;
	bool press_handled;
	bool dirty;
} game_t;

static uint32_t rnd(game_t *g)
{
	uint32_t x = g->rng;
	x ^= x << 13;
	x ^= x >> 17;
	x ^= x << 5;
	return g->rng = x;
}

static const char *tr(const char *pt, const char *en)
{
	return FW_LANG == FW_LANG_PT ? pt : en;
}

static const char *snake_name(void)
{
	return tr("Cobrinha", "Snake");
}

static void set_score(game_t *g)
{
	char buf[16];
	char *p = fw_put_str(buf, tr("Pontos ", "Score "));
	fw_put_dec(p, g->score);
	lv_label_set_text(g->score_label, buf);
}

static void show_message(game_t *g, const char *title, const char *text)
{
	lv_label_set_text(g->msg_title, title);
	lv_label_set_text(g->msg_text, text);
	lv_obj_align(g->msg_title, LV_ALIGN_TOP_MID, 0, 4);
	lv_obj_align(g->msg_text, LV_ALIGN_TOP_MID, 0, 24);
	lv_obj_clear_flag(g->msg, LV_OBJ_FLAG_HIDDEN);
}

static void hide_message(game_t *g)
{
	lv_obj_add_flag(g->msg, LV_OBJ_FLAG_HIDDEN);
}

static bool occupied(game_t *g, uint8_t x, uint8_t y)
{
	for (uint16_t i = 0; i < g->len; i++)
		if (g->body[i].x == x && g->body[i].y == y)
			return true;
	return false;
}

static void place_food(game_t *g)
{
	for (int n = 0; n < MAX_CELLS; n++) {
		uint8_t x = (uint8_t)(rnd(g) % COLS);
		uint8_t y = (uint8_t)(rnd(g) % ROWS);
		if (!occupied(g, x, y)) {
			g->food_x = x;
			g->food_y = y;
			return;
		}
	}
	g->food_x = 0xFF;
	g->food_y = 0xFF;
}

static void fill_cell(uint8_t *px, int x, int y, uint8_t color)
{
	uint8_t *p = px + y * CELL * (FIELD_W / 2) + x * (CELL / 2);
	uint8_t v = (uint8_t)((color << 4) | color);
	for (int r = 0; r < CELL; r++)
		memset(p + r * (FIELD_W / 2), v, CELL / 2);
}

static void render(game_t *g)
{
	uint8_t *px = g->px + PALETTE_SIZE;
	memset(px, 0, FIELD_W / 2 * FIELD_H);
	if (g->food_x < COLS && g->food_y < ROWS)
		fill_cell(px, g->food_x, g->food_y, C_FOOD);
	for (uint16_t i = g->len; i > 0; i--) {
		cell_t c = g->body[i - 1];
		fill_cell(px, c.x, c.y, i == 1 ? C_HEAD : C_SNAKE);
	}
	lv_obj_invalidate(g->img);
}

static void game_over(game_t *g)
{
	g->state = OVER;
	g->state_ms = 0;
	char buf[48];
	char *p = fw_put_str(buf, tr("Pontos ", "Score "));
	p = fw_put_dec(p, g->score);
	fw_put_str(p, tr("\n\nPlay: recomeçar", "\n\nPlay: restart"));
	show_message(g, tr("Fim de jogo", "Game over"), buf);
	g->dirty = true;
}

static void reset_round(game_t *g)
{
	uint8_t cx = COLS / 2, cy = ROWS / 2;
	g->rng ^= lv_tick_get();
	if (!g->rng)
		g->rng = 1;
	g->len = START_LEN;
	g->dir = 0;
	g->next_dir = 0;
	for (uint16_t i = 0; i < START_LEN; i++) {
		g->body[i].x = (uint8_t)(cx - i);
		g->body[i].y = cy;
	}
	g->score = 0;
	g->speed_ms = START_MS;
	g->acc = 0;
	g->state = READY;
	g->state_ms = 0;
	g->last_back = 0;
	place_food(g);
	set_score(g);
	lv_obj_align(g->msg_title, LV_ALIGN_TOP_MID, 0, 4);
	show_message(g, snake_name(),
		     tr("Play: começar\n<< >>: virar\nVOL 2x: sair",
			"Play: start\n<< >>: turn\nVOL 2x: exit"));
	g->dirty = true;
}

static void step(game_t *g)
{
	static const int8_t dx[] = {1, 0, -1, 0};
	static const int8_t dy[] = {0, 1, 0, -1};

	g->dir = g->next_dir;
	int nx = g->body[0].x + dx[g->dir];
	int ny = g->body[0].y + dy[g->dir];
	if (nx < 0 || nx >= COLS || ny < 0 || ny >= ROWS) {
		game_over(g);
		return;
	}
	bool eating = (nx == g->food_x && ny == g->food_y);
	uint16_t limit = (uint16_t)(eating ? g->len : g->len - 1);
	for (uint16_t i = 0; i < limit; i++) {
		if (g->body[i].x == nx && g->body[i].y == ny) {
			game_over(g);
			return;
		}
	}
	if (eating && g->len < MAX_CELLS)
		g->len++;
	for (uint16_t i = (uint16_t)(g->len - 1); i > 0; i--)
		g->body[i] = g->body[i - 1];
	g->body[0].x = (uint8_t)nx;
	g->body[0].y = (uint8_t)ny;
	if (eating) {
		g->score++;
		if (g->speed_ms > MIN_MS) {
			g->speed_ms -= SPEED_STEP_MS;
			if (g->speed_ms < MIN_MS)
				g->speed_ms = MIN_MS;
		}
		set_score(g);
		place_food(g);
	}
	g->dirty = true;
}

static void play_action(game_t *g)
{
	switch (g->state) {
	case READY:
		hide_message(g);
		g->state = PLAYING;
		g->state_ms = 0;
		g->acc = 0;
		break;
	case PLAYING:
		g->state = PAUSED;
		show_message(g, tr("Pausa", "Paused"),
			     tr("Play: continuar", "Play: resume"));
		break;
	case PAUSED:
		hide_message(g);
		g->state = PLAYING;
		g->acc = 0;
		break;
	case OVER:
		if (g->state_ms >= RETRY_DELAY_MS) {
			reset_round(g);
			hide_message(g);
			g->state = PLAYING;
			g->acc = 0;
		}
		break;
	}
}

static void turn(game_t *g, uint8_t delta)
{
	if (g->state != PLAYING || g->next_dir != g->dir)
		return;
	uint8_t d = (uint8_t)((g->dir + delta) & 3);
	if (d == ((g->dir + 2) & 3))
		return;
	g->next_dir = d;
}

static void tick_cb(lv_timer_t *t)
{
	game_t *g = t->user_data;
	uint32_t now = lv_tick_get();
	uint32_t dt = now - g->last_tick;
	g->last_tick = now;
	dt = dt > MAX_DT ? MAX_DT : dt;
	g->state_ms += dt;
	if (g->state == PLAYING) {
		g->acc += dt;
		while (g->acc >= g->speed_ms && g->state == PLAYING) {
			g->acc -= g->speed_ms;
			step(g);
		}
	}
	if (g->dirty) {
		g->dirty = false;
		render(g);
	}
}

static void input_cb(lv_event_t *e)
{
	game_t *g = lv_event_get_user_data(e);
	uint8_t code = lv_event_get_code(e);
	if (code == LV_EVENT_PRESSED) {
		g->press_handled = true;
		play_action(g);
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
	switch (key) {
	case FW_KEY_PREV:
	case FW_KEY_PREV_LONG:
		turn(g, 3);
		break;
	case FW_KEY_NEXT:
	case FW_KEY_NEXT_LONG:
		turn(g, 1);
		break;
	case FW_KEY_PLAY:
		if (g->press_handled)
			g->press_handled = false;
		else
			play_action(g);
		break;
	}
}

static void on_delete(void *ctx)
{
	game_t *g = ctx;
	if (g->timer)
		lv_timer_del(g->timer);
	lv_mem_free(g);
}

static void set_palette(uint8_t *pal)
{
	static const uint8_t rgb[4][3] = {
		{0x00, 0x00, 0x00},
		{0x78, 0xDC, 0x78},
		{0xFF, 0x52, 0x52},
		{0xA0, 0xFF, 0xA0},
	};
	memset(pal, 0, PALETTE_SIZE);
	for (int i = 0; i < 4; i++) {
		pal[i * 4 + 0] = rgb[i][2];
		pal[i * 4 + 1] = rgb[i][1];
		pal[i * 4 + 2] = rgb[i][0];
		pal[i * 4 + 3] = 0xFF;
	}
}

static void build_scene(game_t *g, lv_obj_t *root)
{
	lv_coord_t w = lv_disp_get_hor_res(NULL);

	g->score_label = fw_label(root, "", COLOR_SNAKE);
	lv_obj_set_width(g->score_label, (lv_coord_t)(w - 4));
	lv_obj_set_pos(g->score_label, 2, 0);

	set_palette(g->px);
	memset(g->px + PALETTE_SIZE, 0, IMG_SIZE - PALETTE_SIZE);
	g->dsc.header = LV_IMG_HEADER(LV_IMG_CF_INDEXED_4BIT, FIELD_W, FIELD_H);
	g->dsc.data_size = IMG_SIZE;
	g->dsc.data = g->px;
	g->img = lv_img_create(root);
	lv_img_set_src(g->img, &g->dsc);
	lv_obj_set_pos(g->img, 0, HUD_H);

	g->msg = fw_rect(root, (lv_coord_t)(w - 16), 66, lv_rgb(0x00, 0x00, 0x00));
	lv_obj_set_style_border_width(g->msg, 1, 0);
	lv_obj_set_style_border_color(g->msg, COLOR_SNAKE, 0);
	lv_obj_set_pos(g->msg, 8, (lv_coord_t)(HUD_H + (FIELD_H - 66) / 2));
	g->msg_title = fw_label(g->msg, "", COLOR_SNAKE);
	g->msg_text = fw_label(g->msg, "", COLOR_TEXT);
	lv_obj_set_style_text_align(g->msg_text, LV_TEXT_ALIGN_CENTER, 0);
	lv_obj_align(g->msg_title, LV_ALIGN_TOP_MID, 0, 4);
	lv_obj_align(g->msg_text, LV_ALIGN_TOP_MID, 0, 24);
}

void cobrinha_open(lv_obj_t *return_focus)
{
	game_t *g = lv_mem_alloc(sizeof(game_t));
	if (!g)
		return;
	memset(g, 0, sizeof(*g));
	g->rng = FW_SYSTICK_VAL ^ 0x9E3779B9u;
	if (!g->rng)
		g->rng = 1;

	g->ov = fw_overlay_open(return_focus, lv_rgb(0, 0, 0), on_delete, g);
	if (!g->ov) {
		lv_mem_free(g);
		return;
	}
	build_scene(g, g->ov->root);
	reset_round(g);
	render(g);
	g->dirty = false;

	lv_obj_add_event_cb(g->ov->root, input_cb, LV_EVENT_PRESSED, g);
	lv_obj_add_event_cb(g->ov->root, input_cb, LV_EVENT_KEY, g);
	g->last_tick = lv_tick_get();
	g->timer = lv_timer_create(tick_cb, TICK_MS, g);
}
