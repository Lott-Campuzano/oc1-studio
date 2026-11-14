{
	"patcher" :	{
		"fileformatversion" : 1,
		"appversion" :	{
			"major" : 8,
			"minor" : 6,
			"revision" : 5,
			"architecture" : "x64",
			"modernui" : 1
		},
		"rect" : [ 100.0, 100.0, 660.0, 420.0 ],
		"gridsize" : [ 8.0, 8.0 ],
		"default_fontsize" : 12.0,
		"default_fontname" : "Arial",
		"boxes" : [			{
				"box" :				{
					"id" : "obj-14",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 32.0, 24.0, 560.0, 22.0 ],
					"text" : "OP-1 STUDIO ↔ Ableton · notas UDP:7647 → MIDI out · reloj 16avos → UDP:7648"
				}

			}
,			{
				"box" :				{
					"id" : "obj-1",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 32.0, 80.0, 130.0, 24.0 ],
					"text" : "udpreceive 7647"
				}

			}
,			{
				"box" :				{
					"id" : "obj-2",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "" ],
					"patching_rect" : [ 32.0, 116.0, 100.0, 24.0 ],
					"text" : "route op1"
				}

			}
,			{
				"box" :				{
					"id" : "obj-3",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "" ],
					"patching_rect" : [ 32.0, 152.0, 100.0, 24.0 ],
					"text" : "route note"
				}

			}
,			{
				"box" :				{
					"id" : "obj-4",
					"maxclass" : "newobj",
					"numinlets" : 3,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 32.0, 188.0, 110.0, 24.0 ],
					"text" : "makenote 150"
				}

			}
,			{
				"box" :				{
					"id" : "obj-5",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 32.0, 224.0, 90.0, 24.0 ],
					"text" : "pack 60 100"
				}

			}
,			{
				"box" :				{
					"id" : "obj-6",
					"maxclass" : "newobj",
					"numinlets" : 7,
					"numoutlets" : 1,
					"outlettype" : [ "int" ],
					"patching_rect" : [ 32.0, 260.0, 90.0, 24.0 ],
					"text" : "midiformat"
				}

			}
,			{
				"box" :				{
					"id" : "obj-7",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 32.0, 296.0, 90.0, 24.0 ],
					"text" : "midiout"
				}

			}
,			{
				"box" :				{
					"id" : "obj-8",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 360.0, 80.0, 90.0, 24.0 ],
					"text" : "transport"
				}

			}
,			{
				"box" :				{
					"id" : "obj-9",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 360.0, 116.0, 100.0, 24.0 ],
					"text" : "round 120"
				}

			}
,			{
				"box" :				{
					"id" : "obj-10",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 360.0, 152.0, 80.0, 24.0 ],
					"text" : "change"
				}

			}
,			{
				"box" :				{
					"id" : "obj-11",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 360.0, 188.0, 190.0, 24.0 ],
					"text" : "expr (int($f1 / 120.) % 16)"
				}

			}
,			{
				"box" :				{
					"id" : "obj-12",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 360.0, 224.0, 140.0, 24.0 ],
					"text" : "prepend op1 clock"
				}

			}
,			{
				"box" :				{
					"id" : "obj-13",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 360.0, 260.0, 170.0, 24.0 ],
					"text" : "udpsend 127.0.0.1 7648"
				}

			}
 ],
		"lines" : [			{
				"patchline" :				{
					"destination" : [ "obj-2", 0 ],
					"source" : [ "obj-1", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-3", 0 ],
					"source" : [ "obj-2", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-4", 0 ],
					"source" : [ "obj-3", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-5", 0 ],
					"source" : [ "obj-4", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-5", 1 ],
					"source" : [ "obj-4", 1 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-6", 0 ],
					"source" : [ "obj-5", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-7", 0 ],
					"source" : [ "obj-6", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-9", 0 ],
					"source" : [ "obj-8", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-10", 0 ],
					"source" : [ "obj-9", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-11", 0 ],
					"source" : [ "obj-10", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-12", 0 ],
					"source" : [ "obj-11", 0 ]
				}

			}
,			{
				"patchline" :				{
					"destination" : [ "obj-13", 0 ],
					"source" : [ "obj-12", 0 ]
				}

			}
 ]
	}

}
