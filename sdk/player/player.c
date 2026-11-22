/* Player card on the home page (Reload 3.5, ficha 028).
 *
 * The title is already delivered to the ViewTask (CPU1) as a type 3
 * message.  We copy it from the two label_process hooks (player page and
 * home page) and show it on a small card.  The state lives in the
 * user_data of a timer that is created once and never deleted; the hooks
 * find it by walking the LVGL timer list, so there is no .data/.bss and
 * no fixed RAM slot.
 *
 * No kernel, database, FatFs or get_path is called here.
 */
#include "sdk.h"

#define FW_PLAYER_MAGIC 0x4F503335u
#define FW_TIMER_LL 0x0081D2D4u
#define FW_VIEW_CTX_PTR 0x0081CE2Cu
#define FW_VIEW_PAGE4_OFF 0xACu
#define FW_HOME_PAGE_MAIN_OFF 0x48u
#define FW_TITLE_MAX 64u

typedef struct {
	uint32_t magic;
	char title[FW_TITLE_MAX];
	uint32_t version;
	uint32_t shown_version;
	lv_obj_t *card;
	lv_obj_t *title_label;
} fw_player_state_t;

static void fw_player_timer_cb(lv_timer_t *t);

static fw_player_state_t *fw_player_find_state(void)
{
	uint32_t n = *(volatile uint32_t *)FW_TIMER_LL;
	void *node = *(void **)(FW_TIMER_LL + 4);
	uintptr_t want = (uintptr_t)fw_player_timer_cb & ~(uintptr_t)1;

	while (node) {
		lv_timer_t *t = (lv_timer_t *)node;
		if (((uintptr_t)t->timer_cb & ~(uintptr_t)1) == want) {
			fw_player_state_t *st = t->user_data;
			if (st && st->magic == FW_PLAYER_MAGIC)
				return st;
		}
		node = *(void **)((uint8_t *)node + n + 4);
	}
	return NULL;
}

static void fw_player_set_title(const char *text)
{
	fw_player_state_t *st = fw_player_find_state();
	size_t n;

	if (!st)
		return;
	if (!text)
		text = "";
	n = strlen(text);
	if (n > FW_TITLE_MAX - 1)
		n = FW_TITLE_MAX - 1;
	memcpy(st->title, text, n);
	st->title[n] = 0;
	st->version++;
}

/* Copies the title to the card only for the label at [page4_view+0] (the
 * others, +4/+8/+0x14/+0x18, are artist/album/...).  Called by the wrappers
 * below, never by the factory directly. */
__attribute__((used, noinline))
static void fw_player_title_update(lv_obj_t *label, const char *text)
{
	uint8_t *ctx = *(uint8_t **)FW_VIEW_CTX_PTR;
	void *view = ctx ? *(void **)(ctx + FW_VIEW_PAGE4_OFF) : NULL;

	if (view && label == *(lv_obj_t **)view)
		fw_player_set_title(text);
}

/* Patched over 0xD3225E (3.3: `b.w 0xDAA014`, the cover TITULO entry).
 * Saves r0/r1 and the caller's LR, updates the card, then tail-branches to
 * the factory TITULO so the cover still loads.  The caller's LR survives:
 * the `b.w` does not touch it. */
__attribute__((naked)) void fw_player_title_hook(void)
{
	__asm__ volatile(
		"push {r0, r1, r2, lr}\n"
		"bl fw_player_title_update\n"
		"pop {r0, r1, r2, lr}\n"
		"b.w .\n");
}

/* Home label_process receives the same type 3 while the home is open. */
void fw_player_title_hook_home(void *msg)
{
	if (!msg)
		return;
	fw_player_set_title((const char *)msg + 0x14);
}

/* Patched over 0xD2EEE4 with a `b.w` (not `bl`): the page_home_label_process
 * is a leaf and its caller's LR must survive.  The 4-byte window covers the
 * factory `ldr r3,[pc]; ldrb r3,[r3]`; we redo both, then tail-branch to
 * 0xD2EEE8 (the factory `cmp r3,#3`).  r0-r4 and LR are saved/restored; six
 * words keep the stack 8-byte aligned. */
__attribute__((naked)) void fw_player_title_hook_home_wrap(void)
{
	__asm__ volatile(
		"push {r0, r1, r2, r3, r4, lr}\n"
		"bl fw_player_title_hook_home\n"
		"pop {r0, r1, r2, r3, r4, lr}\n"
		"movw r3, #0x3EB0\n"
		"movt r3, #0x0082\n"
		"ldrb r3, [r3]\n"
		"b.w .\n");
}

static void fw_player_card_delete_cb(lv_event_t *e)
{
	fw_player_state_t *st = lv_event_get_user_data(e);
	if (st) {
		st->card = NULL;
		st->title_label = NULL;
	}
}

static const char *fw_player_empty(void)
{
	return FW_LANG == FW_LANG_PT ? "Nada tocando" : "Nothing playing";
}

static void fw_player_note(lv_obj_t *card, lv_color_t color)
{
	lv_obj_t *head = fw_rect(card, 7, 5, color);
	lv_obj_t *stem = fw_rect(card, 2, 9, color);
	lv_obj_t *flag = fw_rect(card, 5, 2, color);

	if (head) {
		lv_obj_set_style_radius(head, 3, 0);
		lv_obj_set_pos(head, 4, 11);
	}
	if (stem)
		lv_obj_set_pos(stem, 8, 4);
	if (flag)
		lv_obj_set_pos(flag, 8, 4);
}

static void fw_player_create_card(fw_player_state_t *st)
{
	void *page = fw_view_page();
	lv_obj_t *parent = page ? *(lv_obj_t **)((uint8_t *)page +
						 FW_HOME_PAGE_MAIN_OFF) : NULL;
	lv_obj_t *card;
	lv_obj_t *title;

	if (!parent)
		parent = lv_disp_get_scr_act(NULL);
	if (!parent)
		return;
	card = lv_obj_create(parent);
	if (!card)
		return;
	lv_obj_set_size(card, 112, 22);
	lv_obj_set_pos(card, 8, 136);
	lv_obj_clear_flag(card, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);
	lv_obj_set_style_radius(card, 4, 0);
	lv_obj_set_style_border_width(card, 0, 0);
	lv_obj_set_style_bg_color(card, lv_rgb(26, 26, 28), 0);
	lv_obj_set_style_bg_opa(card, 255, 0);
	lv_obj_set_style_pad_top(card, 0, 0);
	lv_obj_set_style_pad_bottom(card, 0, 0);
	lv_obj_set_style_pad_left(card, 0, 0);
	lv_obj_set_style_pad_right(card, 0, 0);
	fw_player_note(card, lv_rgb(180, 246, 131));

	title = fw_label(card, st->title[0] ? st->title : fw_player_empty(),
			 lv_rgb(230, 230, 235));
	if (title) {
		lv_obj_set_width(title, 94);
		lv_label_set_long_mode(title, LV_LABEL_LONG_DOT);
		lv_obj_set_pos(title, 17, 5);
	}
	st->card = card;
	st->title_label = title;
	st->shown_version = st->version;
	lv_obj_add_event_cb(card, fw_player_card_delete_cb, LV_EVENT_DELETE, st);
}

static void fw_player_timer_cb(lv_timer_t *t)
{
	fw_player_state_t *st = t->user_data;

	if (!st || !st->card || !st->title_label)
		return;
	if (st->shown_version != st->version) {
		lv_label_set_text(st->title_label,
				  st->title[0] ? st->title : fw_player_empty());
		st->shown_version = st->version;
	}
}

/* Patched over page_home_create's bl (0xD23B8C). */
int hook_home_create(void)
{
	int ret = FW_HOME_PAGE_CREATE();
	fw_player_state_t *st;

	if (ret)
		return ret;
	st = fw_player_find_state();
	if (!st) {
		lv_timer_t *timer;
		st = lv_mem_alloc(sizeof(*st));
		if (!st)
			return 0;
		memset(st, 0, sizeof(*st));
		st->magic = FW_PLAYER_MAGIC;
		st->version = 1;
		timer = lv_timer_create(fw_player_timer_cb, 500, st);
		if (!timer) {
			lv_mem_free(st);
			return 0;
		}
	}
	fw_player_create_card(st);
	return 0;
}
