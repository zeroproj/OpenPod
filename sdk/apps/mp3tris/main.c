/*
 * Mp3tris: falling-block puzzle.  Left/Right move, Up rotates, a Center
 * press drops the piece one row, holding Center drops it to the bottom,
 * Back twice exits.  Runs as a full-screen overlay opened from the
 * Applications menu.
 *
 * The board and the next-piece preview are 16-color images in RAM that are
 * redrawn in place; one object per cell would not fit in the 40 KB LVGL
 * heap.
 *
 * Based on the SL6801_player SDK by Dmitry Brant, used with permission.
 */
#include "sdk.h"

#define COLS 10
#define ROWS 20
#define CELL 7
#define BOARD_W (COLS * CELL)
#define BOARD_H (ROWS * CELL)
#define NEXT_W (4 * CELL)
#define NEXT_H (2 * CELL)
#define PALETTE_SIZE (16 * 4)

#define TICK_MS 16
#define MAX_DT 100
#define LOCK_MS 450
#define MAX_LOCK_RESETS 15
#define CLEAR_MS 300
#define RETRY_DELAY_MS 700
#define BACK_EXIT_MS 800

#define PAL_BOARD 0
#define PAL_LIGHT 7
#define PAL_WHITE 15

#define COLOR_BG lv_rgb(0x0A, 0x0C, 0x16)
#define COLOR_FRAME lv_rgb(0x4A, 0x5A, 0x8A)
#define COLOR_PANEL lv_rgb(0x14, 0x18, 0x28)
#define COLOR_HEAD lv_rgb(0x8C, 0x9C, 0xC8)
#define COLOR_TEXT lv_rgb(0xFF, 0xFF, 0xFF)
#define COLOR_TITLE lv_rgb(0xF2, 0xC1, 0x4E)

enum { READY, PLAYING, CLEARING, OVER };
enum { P_I, P_O, P_T, P_S, P_Z, P_J, P_L, P_COUNT };

static const uint8_t board_rgb[3] = {0x14, 0x18, 0x28};
static const uint8_t piece_rgb[P_COUNT][2][3] = {
	{{0x2E, 0xC4, 0xB6}, {0x9E, 0xF0, 0xE6}},
	{{0xF2, 0xC1, 0x4E}, {0xFF, 0xEC, 0xA8}},
	{{0xC0, 0x5C, 0xE0}, {0xE6, 0xB0, 0xF6}},
	{{0x7C, 0xCB, 0x3E}, {0xC8, 0xF0, 0x9A}},
	{{0xF0, 0x60, 0x50}, {0xFF, 0xB4, 0xA8}},
	{{0x5A, 0x78, 0xF0}, {0xB0, 0xC0, 0xFF}},
	{{0xF5, 0x8E, 0x2A}, {0xFF, 0xCC, 0x90}},
};

static const int8_t shapes[P_COUNT][4][2] = {
	{{0, 1}, {1, 1}, {2, 1}, {3, 1}},
	{{0, 0}, {1, 0}, {0, 1}, {1, 1}},
	{{1, 0}, {0, 1}, {1, 1}, {2, 1}},
	{{1, 0}, {2, 0}, {0, 1}, {1, 1}},
	{{0, 0}, {1, 0}, {1, 1}, {2, 1}},
	{{0, 0}, {0, 1}, {1, 1}, {2, 1}},
	{{2, 0}, {0, 1}, {1, 1}, {2, 1}},
};
static const uint8_t box_size[P_COUNT] = {4, 2, 3, 3, 3, 3, 3};

static const int8_t kicks[][2] = {{0, 0}, {-1, 0}, {1, 0}, {0, -1}, {-2, 0}, {2, 0}};

static const uint16_t fall_ms[] = {800, 720, 630, 550, 470, 380, 300, 220, 160, 120, 100, 90, 80, 70, 60, 50};
static const uint16_t line_points[5] = {0, 100, 300, 500, 800};

typedef struct {
	int8_t x, y;
} cell_t;

typedef struct {
	fw_overlay_t *ov;
	lv_timer_t *timer;
	lv_obj_t *board_img, *next_img;
	lv_obj_t *score_val, *lines_val, *level_val;
	lv_obj_t *msg, *msg_title, *msg_text;
	lv_img_dsc_t board_dsc, next_dsc;
	uint8_t board_px[PALETTE_SIZE + BOARD_W / 2 * BOARD_H];
	uint8_t next_px[PALETTE_SIZE + NEXT_W / 2 * NEXT_H];

	uint8_t board[ROWS][COLS];
	uint8_t type, rot, next;
	int8_t px, py;
	uint8_t bag[P_COUNT], bag_left;
	uint32_t full_rows;

	uint32_t rng, last_tick;
	uint32_t fall_acc, lock_ms, state_ms;
	uint32_t score, best;
	uint32_t last_back;
	uint16_t lines;
	uint8_t level, lock_resets, state;
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

static void piece_cells(uint8_t type, uint8_t rot, cell_t out[4])
{
	int n = box_size[type];
	for (int i = 0; i < 4; i++) {
		int x = shapes[type][i][0], y = shapes[type][i][1];
		for (int r = 0; r < rot; r++) {
			int t = x;
			x = n - 1 - y;
			y = t;
		}
		out[i].x = (int8_t)x;
		out[i].y = (int8_t)y;
	}
}

static bool fits(game_t *g, uint8_t rot, int px, int py)
{
	cell_t c[4];
	piece_cells(g->type, rot, c);
	for (int i = 0; i < 4; i++) {
		int x = px + c[i].x, y = py + c[i].y;
		if (x < 0 || x >= COLS || y >= ROWS)
			return false;
		if (y >= 0 && g->board[y][x])
			return false;
	}
	return true;
}

static uint8_t bag_next(game_t *g)
{
	if (!g->bag_left) {
		for (int i = 0; i < P_COUNT; i++)
			g->bag[i] = (uint8_t)i;
		for (int i = P_COUNT - 1; i > 0; i--) {
			int j = (int)(rnd(g) % (uint32_t)(i + 1));
			uint8_t t = g->bag[i];
			g->bag[i] = g->bag[j];
			g->bag[j] = t;
		}
		g->bag_left = P_COUNT;
	}
	return g->bag[--g->bag_left];
}

static void put_px(uint8_t *px, int stride, int x, int y, uint8_t c)
{
	uint8_t *b = px + y * stride + (x >> 1);
	*b = (x & 1) ? (uint8_t)((*b & 0xF0) | c) : (uint8_t)((*b & 0x0F) | (c << 4));
}

static void draw_block(uint8_t *px, int stride, int x0, int y0, uint8_t type)
{
	uint8_t base = (uint8_t)(1 + type), light = (uint8_t)(1 + PAL_LIGHT + type);
	for (int y = 0; y < CELL - 1; y++)
		for (int x = 0; x < CELL - 1; x++)
			put_px(px, stride, x0 + x, y0 + y, (x == 0 || y == 0) ? light : base);
}

static void draw_ghost(uint8_t *px, int stride, int x0, int y0, uint8_t type)
{
	for (int y = 0; y < CELL - 1; y++)
		for (int x = 0; x < CELL - 1; x++)
			if ((x == 0 || y == 0 || x == CELL - 2 || y == CELL - 2) && !((x + y) & 1))
				put_px(px, stride, x0 + x, y0 + y, (uint8_t)(1 + type));
}

static void fill_row(uint8_t *px, int stride, int y0, uint8_t c)
{
	memset(px + y0 * stride, (c << 4) | c, (size_t)(stride * (CELL - 1)));
}

static void render_board(game_t *g)
{
	uint8_t *px = g->board_px + PALETTE_SIZE;
	const int stride = BOARD_W / 2;
	memset(px, 0, stride * BOARD_H);
	bool blink_on = g->state == CLEARING && (g->state_ms / 75) % 2 == 0;
	for (int y = 0; y < ROWS; y++) {
		if ((g->full_rows >> y) & 1 && blink_on) {
			fill_row(px, stride, y * CELL, PAL_WHITE);
			continue;
		}
		for (int x = 0; x < COLS; x++)
			if (g->board[y][x])
				draw_block(px, stride, x * CELL, y * CELL, (uint8_t)(g->board[y][x] - 1));
	}
	if (g->state == PLAYING) {
		cell_t c[4];
		piece_cells(g->type, g->rot, c);
		int gy = g->py;
		while (fits(g, g->rot, g->px, gy + 1))
			gy++;
		for (int i = 0; i < 4; i++) {
			int x = g->px + c[i].x, y = gy + c[i].y;
			if (gy != g->py && y >= 0)
				draw_ghost(px, stride, x * CELL, y * CELL, g->type);
		}
		for (int i = 0; i < 4; i++) {
			int x = g->px + c[i].x, y = g->py + c[i].y;
			if (y >= 0)
				draw_block(px, stride, x * CELL, y * CELL, g->type);
		}
	}
	lv_obj_invalidate(g->board_img);
}

static void render_next(game_t *g)
{
	uint8_t *px = g->next_px + PALETTE_SIZE;
	const int stride = NEXT_W / 2;
	memset(px, 0, stride * NEXT_H);
	if (g->state != READY) {
		cell_t c[4];
		piece_cells(g->next, 0, c);
		int x0 = 4, x1 = 0, y0 = 4, y1 = 0;
		for (int i = 0; i < 4; i++) {
			x0 = c[i].x < x0 ? c[i].x : x0;
			x1 = c[i].x > x1 ? c[i].x : x1;
			y0 = c[i].y < y0 ? c[i].y : y0;
			y1 = c[i].y > y1 ? c[i].y : y1;
		}
		int ox = (NEXT_W - (x1 - x0 + 1) * CELL + 1) / 2, oy = (NEXT_H - (y1 - y0 + 1) * CELL + 1) / 2;
		for (int i = 0; i < 4; i++)
			draw_block(px, stride, ox + (c[i].x - x0) * CELL, oy + (c[i].y - y0) * CELL, g->next);
	}
	lv_obj_invalidate(g->next_img);
}

static void set_num(lv_obj_t *label, uint32_t v)
{
	char buf[12];
	fw_put_dec(buf, v);
	lv_label_set_text(label, buf);
}

static void update_stats(game_t *g)
{
	set_num(g->score_val, g->score);
	set_num(g->lines_val, g->lines);
	set_num(g->level_val, g->level);
}

static void show_message(game_t *g, const char *title, const char *text)
{
	lv_label_set_text(g->msg_title, title);
	lv_label_set_text(g->msg_text, text);
	lv_obj_align(g->msg_title, LV_ALIGN_TOP_MID, 0, 6);
	lv_obj_align(g->msg_text, LV_ALIGN_TOP_MID, 0, 26);
	lv_obj_clear_flag(g->msg, LV_OBJ_FLAG_HIDDEN);
}

static void game_over(game_t *g)
{
	g->state = OVER;
	g->state_ms = 0;
	if (g->score > g->best)
		g->best = g->score;
	char buf[64];
	char *p = fw_put_str(buf, "Score ");
	p = fw_put_dec(p, g->score);
	p = fw_put_str(p, "\nBest ");
	p = fw_put_dec(p, g->best);
	fw_put_str(p, "\n\nCenter: again");
	show_message(g, "Fim de jogo", buf);
	g->dirty = true;
}

static void spawn(game_t *g)
{
	g->type = g->next;
	g->next = bag_next(g);
	g->rot = 0;
	g->px = (int8_t)((COLS - box_size[g->type]) / 2);
	g->py = g->type == P_I ? -1 : 0;
	g->fall_acc = 0;
	g->lock_ms = 0;
	g->lock_resets = 0;
	g->state = PLAYING;
	g->dirty = true;
	render_next(g);
	if (!fits(g, g->rot, g->px, g->py))
		game_over(g);
}

static void start(game_t *g)
{
	memset(g->board, 0, sizeof(g->board));
	g->rng ^= lv_tick_get();
	g->bag_left = 0;
	g->score = 0;
	g->lines = 0;
	g->level = 1;
	g->full_rows = 0;
	g->last_back = 0;
	g->next = bag_next(g);
	update_stats(g);
	lv_obj_add_flag(g->msg, LV_OBJ_FLAG_HIDDEN);
	spawn(g);
}

static void lock_piece(game_t *g)
{
	cell_t c[4];
	piece_cells(g->type, g->rot, c);
	bool above = false;
	for (int i = 0; i < 4; i++) {
		int x = g->px + c[i].x, y = g->py + c[i].y;
		if (y < 0)
			above = true;
		else
			g->board[y][x] = (uint8_t)(g->type + 1);
	}
	g->dirty = true;
	if (above) {
		game_over(g);
		return;
	}
	g->full_rows = 0;
	int n = 0;
	for (int y = 0; y < ROWS; y++) {
		int x = 0;
		while (x < COLS && g->board[y][x])
			x++;
		if (x == COLS) {
			g->full_rows |= 1u << y;
			n++;
		}
	}
	if (!n) {
		spawn(g);
		return;
	}
	g->lines += (uint16_t)n;
	g->score += line_points[n] * g->level;
	uint8_t level = (uint8_t)(1 + g->lines / 10);
	g->level = level;
	update_stats(g);
	g->state = CLEARING;
	g->state_ms = 0;
}

static void remove_full_rows(game_t *g)
{
	int dst = ROWS - 1;
	for (int y = ROWS - 1; y >= 0; y--)
		if (!((g->full_rows >> y) & 1)) {
			if (dst != y)
				memcpy(g->board[dst], g->board[y], COLS);
			dst--;
		}
	for (; dst >= 0; dst--)
		memset(g->board[dst], 0, COLS);
	g->full_rows = 0;
}

static bool grounded(game_t *g)
{
	return !fits(g, g->rot, g->px, g->py + 1);
}

static void moved(game_t *g)
{
	if (grounded(g) && g->lock_resets < MAX_LOCK_RESETS) {
		g->lock_ms = 0;
		g->lock_resets++;
	}
	g->dirty = true;
}

static void shift(game_t *g, int dx)
{
	if (g->state == PLAYING && fits(g, g->rot, g->px + dx, g->py)) {
		g->px = (int8_t)(g->px + dx);
		moved(g);
	}
}

static void rotate(game_t *g)
{
	if (g->state != PLAYING)
		return;
	uint8_t rot = (uint8_t)((g->rot + 1) & 3);
	for (unsigned i = 0; i < sizeof(kicks) / sizeof(kicks[0]); i++) {
		int x = g->px + kicks[i][0], y = g->py + kicks[i][1];
		if (fits(g, rot, x, y)) {
			g->rot = rot;
			g->px = (int8_t)x;
			g->py = (int8_t)y;
			moved(g);
			return;
		}
	}
}

static void step_down(game_t *g)
{
	if (g->state != PLAYING)
		return;
	if (grounded(g)) {
		lock_piece(g);
		return;
	}
	g->py++;
	g->fall_acc = 0;
	g->lock_ms = 0;
	g->score++;
	set_num(g->score_val, g->score);
	g->dirty = true;
}

static void hard_drop(game_t *g)
{
	if (g->state != PLAYING)
		return;
	while (!grounded(g)) {
		g->py++;
		g->score += 2;
	}
	set_num(g->score_val, g->score);
	lock_piece(g);
}

static void update(game_t *g, uint32_t dt)
{
	g->state_ms += dt;
	if (g->state == CLEARING) {
		g->dirty = true;
		if (g->state_ms >= CLEAR_MS) {
			remove_full_rows(g);
			spawn(g);
		}
		return;
	}
	if (g->state != PLAYING)
		return;

	const unsigned n_levels = sizeof(fall_ms) / sizeof(fall_ms[0]);
	uint32_t interval = fall_ms[g->level <= n_levels ? g->level - 1u : n_levels - 1];

	if (!grounded(g)) {
		g->fall_acc += dt;
		while (g->fall_acc >= interval && !grounded(g)) {
			g->fall_acc -= interval;
			g->py++;
			g->lock_ms = 0;
			g->dirty = true;
		}
		if (grounded(g))
			g->fall_acc = 0;
		return;
	}
	g->lock_ms += dt;
	if (g->lock_ms >= LOCK_MS)
		lock_piece(g);
}

static void tick_cb(lv_timer_t *t)
{
	game_t *g = t->user_data;
	uint32_t now = lv_tick_get();
	uint32_t dt = now - g->last_tick;
	g->last_tick = now;
	update(g, dt > MAX_DT ? MAX_DT : dt);
	if (g->dirty) {
		g->dirty = false;
		render_board(g);
	}
}

static void center_down(game_t *g)
{
	switch (g->state) {
	case READY:
		start(g);
		break;
	case OVER:
		if (g->state_ms >= RETRY_DELAY_MS)
			start(g);
		break;
	case PLAYING:
		step_down(g);
		break;
	}
}

static void input_cb(lv_event_t *e)
{
	game_t *g = lv_event_get_user_data(e);
	uint8_t code = lv_event_get_code(e);
	if (code == LV_EVENT_PRESSED) {
		g->press_handled = true;
		center_down(g);
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
	case FW_KEY_LEFT:
		shift(g, -1);
		break;
	case FW_KEY_RIGHT:
		shift(g, 1);
		break;
	case FW_KEY_UP:
		rotate(g);
		break;
	case FW_KEY_CENTER:
		if (g->press_handled)
			g->press_handled = false;
		else
			center_down(g);
		break;
	case FW_KEY_CENTER_LONG:
		hard_drop(g);
		break;
	}
	if (g->dirty) {
		g->dirty = false;
		render_board(g);
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
	memset(pal, 0, PALETTE_SIZE);
	const uint8_t *rgb[16];
	static const uint8_t white[3] = {0xFF, 0xFF, 0xFF};
	rgb[PAL_BOARD] = board_rgb;
	for (int i = 0; i < P_COUNT; i++) {
		rgb[1 + i] = piece_rgb[i][0];
		rgb[1 + PAL_LIGHT + i] = piece_rgb[i][1];
	}
	rgb[PAL_WHITE] = white;
	for (int i = 0; i < 16; i++) {
		pal[i * 4 + 0] = rgb[i][2];
		pal[i * 4 + 1] = rgb[i][1];
		pal[i * 4 + 2] = rgb[i][0];
		pal[i * 4 + 3] = 0xFF;
	}
}

static lv_obj_t *make_image(lv_obj_t *parent, lv_img_dsc_t *dsc, uint8_t *data, size_t size, int w, int h)
{
	set_palette(data);
	memset(data + PALETTE_SIZE, 0, size - PALETTE_SIZE);
	dsc->header = LV_IMG_HEADER(LV_IMG_CF_INDEXED_4BIT, w, h);
	dsc->data_size = (uint32_t)size;
	dsc->data = data;
	lv_obj_t *img = lv_img_create(parent);
	lv_img_set_src(img, dsc);
	return img;
}

static lv_obj_t *panel_label(lv_obj_t *parent, const char *text, lv_color_t color, lv_coord_t x, lv_coord_t y,
			     lv_coord_t w)
{
	lv_obj_t *l = fw_label(parent, text, color);
	lv_obj_set_width(l, w);
	lv_obj_set_style_text_align(l, LV_TEXT_ALIGN_CENTER, 0);
	lv_obj_set_pos(l, x, y);
	return l;
}

static void build_scene(game_t *g, lv_obj_t *root)
{
	lv_coord_t w = lv_disp_get_hor_res(NULL), h = lv_disp_get_ver_res(NULL);
	lv_coord_t bx = 4, by = (lv_coord_t)((h - BOARD_H) / 2);

	lv_obj_t *frame = fw_rect(root, BOARD_W + 4, BOARD_H + 4, COLOR_PANEL);
	lv_obj_set_style_border_width(frame, 1, 0);
	lv_obj_set_style_border_color(frame, COLOR_FRAME, 0);
	lv_obj_set_pos(frame, bx - 2, by - 2);
	g->board_img = make_image(root, &g->board_dsc, g->board_px, sizeof(g->board_px), BOARD_W, BOARD_H);
	lv_obj_set_pos(g->board_img, bx, by);

	lv_coord_t px = bx + BOARD_W + 4, pw = w - px - 2;
	panel_label(root, "NEXT", COLOR_HEAD, px, by, pw);
	lv_obj_t *next_box = fw_rect(root, NEXT_W + 8, NEXT_H + 8, COLOR_PANEL);
	lv_obj_set_style_border_width(next_box, 1, 0);
	lv_obj_set_style_border_color(next_box, COLOR_FRAME, 0);
	lv_obj_set_pos(next_box, px + (pw - NEXT_W - 8) / 2, by + 16);
	g->next_img = make_image(root, &g->next_dsc, g->next_px, sizeof(g->next_px), NEXT_W, NEXT_H);
	lv_obj_set_pos(g->next_img, px + (pw - NEXT_W) / 2, by + 20);

	panel_label(root, "SCORE", COLOR_HEAD, px, by + 48, pw);
	g->score_val = panel_label(root, "0", COLOR_TEXT, px, by + 62, pw);
	panel_label(root, "LINES", COLOR_HEAD, px, by + 82, pw);
	g->lines_val = panel_label(root, "0", COLOR_TEXT, px, by + 96, pw);
	panel_label(root, "LEVEL", COLOR_HEAD, px, by + 116, pw);
	g->level_val = panel_label(root, "1", COLOR_TEXT, px, by + 130, pw);

	g->msg = fw_rect(root, w - 8, 136, COLOR_PANEL);
	lv_obj_set_style_border_width(g->msg, 1, 0);
	lv_obj_set_style_border_color(g->msg, COLOR_TITLE, 0);
	lv_obj_set_pos(g->msg, 4, (h - 136) / 2);
	g->msg_title = fw_label(g->msg, "", COLOR_TITLE);
	g->msg_text = fw_label(g->msg, "", COLOR_TEXT);
	lv_obj_set_style_text_align(g->msg_text, LV_TEXT_ALIGN_CENTER, 0);
}

void mp3tris_open(lv_obj_t *return_focus)
{
	game_t *g = lv_mem_alloc(sizeof(game_t));
	if (!g)
		return;
	memset(g, 0, sizeof(*g));
	g->rng = FW_SYSTICK_VAL ^ 0x9E3779B9u;
	if (!g->rng)
		g->rng = 1;
	g->level = 1;
	g->ov = fw_overlay_open(return_focus, COLOR_BG, on_delete, g);
	if (!g->ov) {
		lv_mem_free(g);
		return;
	}
	lv_obj_t *root = g->ov->root;
	build_scene(g, root);
	g->state = READY;
	show_message(g, "Mp3tris", "Left/Right: mover\nUp: girar\nCenter: descer\nSegure Center: cair\nBack duas vezes: sair\n\nCenter: comecar");

	lv_obj_add_event_cb(root, input_cb, LV_EVENT_PRESSED, g);
	lv_obj_add_event_cb(root, input_cb, LV_EVENT_RELEASED, g);
	lv_obj_add_event_cb(root, input_cb, LV_EVENT_KEY, g);
	g->last_tick = lv_tick_get();
	g->timer = lv_timer_create(tick_cb, TICK_MS, g);
}
