
from master_materials import(
    constants,
    assets,
    materials
)

from master_materials.unreal_systems import EditorUtilitySubsystem

import unreal


MENU_OWNER = "master_material_system"


@unreal.uclass()
class PythonMenuTool(unreal.ToolMenuEntryScript):
    """
    menu tool base class for python tools
    """
    name = "unique_programmatic_tool_name"
    display_name = "menu display name"
    tool_tip = "tool tip message"

    def __init__(self, menu=None, section="", insert_policy=None):
        """
        initialize this python tool and add it to the given menu's section

        parameters:
            menu: the menu object to add this tool to
            section: the section to group this tool under
            insert_policy: (OPTIONAL) unreal.ToolMenuInsert object to manage how the menu is inserted
        """
        super().__init__()

        if menu:
            # Add the given section if not already present
            menu.add_section(section, section)

            # Initialize the entry data
            self.init_entry(
                owner_name=MENU_OWNER,
                menu=menu.menu_name,
                section=section,
                name=self.name,
                label=self.display_name,
                tool_tip=self.tool_tip
            )

            if insert_policy:
                # Build the entry insert object
                entry = unreal.ToolMenuEntry(
                    name=self.name,
                    type=unreal.MultiBlockType.MENU_ENTRY,
                    insert_position=insert_policy,
                    script_object=self
                )

                # Add this tool to the desired menu
                # this will insert using the given policy
                menu.add_menu_entry(section, entry)

            else:
                # Add this tool to the desired menu
                # this will insert at the bottom of the menu
                menu.add_menu_entry_object(self)


@unreal.uclass()
class UserInputField(unreal.Object):
    """Utility Class to handle the display name user input"""

    display_name = unreal.uproperty(
        str,
        dict(ToolTip="The display name to use for this master material in the Right Click Menu")
    )

    def __init__(self):
        super().__init__()
        

@unreal.uclass()
class ToggleMasterMaterial(PythonMenuTool):
    tool_name = "MarkAsMasterMaterial"
    tool_display_name = "Mark As Master Material"
    tooltip = "Set or Unset this material as a Master Material"
    material = unreal.uproperty(unreal.MaterialInterface)

    @unreal.ufunction(override=True)
    def get_label(self, context):
        if self.material:
            if assets.get_metadata(self.material, constants.META_IS_MASTER_MATERIAL):
                master_material_name = assets.get_metadata(self.material, constants.META_MATERIAL_DISPLAY_NAME)
                return f"Unregister `{master_material_name}`"
            return "Register Master Material"
        return "<no valid material selected>"

    @unreal.ufunction(override=True)
    def execute(self, context):
        if self.material and not assets.get_metadata(self.material, constants.META_IS_MASTER_MATERIAL):

            # Get the display name if it's been previously set on this material
            display_name = assets.get_metadata(
                self.material,
                constants.META_MATERIAL_DISPLAY_NAME,
            )

            # Generate a default name -- removes any M_ prefixes and redundant words
            if not display_name:
                display_name = str(self.material.get_name()).split("M_", 1)[-1]
                replacements = [
                    ["material", ""],
                    ["master", ""],
                    ["__", "_"]
                ]

                # remove redundancies from the default name
                for old_text, new_text in replacements:
                    while True:
                        if old_text in display_name.lower():
                            from_index = display_name.lower().index(old_text)
                            to_index = len(old_text) + from_index
                            display_name = new_text.join([display_name[:from_index], display_name[to_index:]])
                        else:
                            break

                # fix any underscores at either end
                display_name = display_name.lstrip("_").rstrip("_")

            # Pop up message for the user to name this master material
            user_input = unreal.new_object(UserInputField)
            user_input.set_editor_property("display_name", display_name)
            title = f"Master Material Display Name"

            popup_options = unreal.EditorDialogLibraryObjectDetailsViewOptions(
                show_object_name=False,
                allow_search=False,
                min_width=100,
                min_height=60,
                value_column_width_ratio=0.6
            )
            success = unreal.EditorDialog.show_object_details_view(title, user_input, popup_options)

            # register the master material
            if success:
                materials.register_master_material(self.material, user_input.get_editor_property("display_name"))

        elif self.material and assets.get_metadata(self.material, constants.META_IS_MASTER_MATERIAL):
            materials.unregister_master_material(self.material)

        assets.save_asset(self.material)

    @unreal.ufunction(override=True)
    def can_execute(self, context) -> bool:
        content_browser_context = context.find_by_class(unreal.ContentBrowserAssetContextMenuContext)

        selected_materials = [
            obj.get_asset()
            for obj in content_browser_context.selected_assets
            if unreal.MathLibrary.class_is_child_of(obj.get_class(), unreal.Material)
        ]
        if not selected_materials or len(selected_materials) > 1:
            self.material = None
            return False

        selected_material = selected_materials[0]
        self.material = selected_material
        return True


@unreal.uclass()
class ApplyMasterMaterial(PythonMenuTool):
    tool_name = "<Material Name>"
    tool_display_name = "<Display Name>"
    material = unreal.uproperty(unreal.Material)
    display_name = unreal.uproperty(str)

    def __init__(self, material, menu=None, section="", insert_policy=None):
        super().__init__()
        self.tool_name = material.get_name()
        self.tool_display_name = assets.get_metadata(
            material,
            constants.META_MATERIAL_DISPLAY_NAME,
            self.tool_name
        )
        self.material = material
        self.display_name = assets.get_metadata(material, constants.META_MATERIAL_DISPLAY_NAME, material.get_name())
        self.tooltip = f"create a new Material Instance of {self.tool_name}"

        if menu:
            self.init_entry(
                MENU_OWNER,
                menu.get_editor_property("menu_name"),
                section,
                self.tool_name,
                self.display_name,
                self.tooltip
            )
            menu.add_menu_entry_object(self)


    @unreal.ufunction(override=True)
    def execute(self, context):
        selected_materials = unreal.EditorUtilityLibrary.get_selected_assets_of_class(unreal.MaterialInterface)

        # If no materials are selected, just create a new MI in the current folder
        if not selected_materials:
            current_folder = unreal.EditorUtilityLibrary.get_current_content_browser_path()

            new_material_instance = materials.create_new_material_instance(
                current_folder,
                self.material
            )
            package_path = new_material_instance.get_package().get_path_name()
            unreal.EditorUtilityLibrary().sync_browser_to_folders([package_path.rsplit("/", 1)[0]])
            unreal.EditorAssetLibrary().sync_browser_to_objects([package_path])
            return

        # Get the EUW
        EUW_results = assets.find_assets(
            name="CreateFromMasterMaterial",
            exact_match=True,
            class_types=["EditorUtilityWidgetBlueprint"],
            str_in_path="/MasterMaterialSystem/"
        )

        if not EUW_results:
            unreal.log_error(f"Could not find the CreateFromMasterMaterial tool!")
            return
        tool = EUW_results[0].package_name

        # Launch the EUW tool
        widget = EditorUtilitySubsystem.spawn_and_register_tab(
            unreal.EditorAssetLibrary.load_asset(
                tool
            )
        )

        # Populate the EUW
        widget.set_editor_properties({
            "from_material": selected_materials[0],
            "to_material": self.material
        })
        master_material_selector = widget.get_editor_property("master_material_selector")
        master_material_selector.set_selected_option(self.display_name)
        widget.call_method("populate", (self.material,))

    @unreal.ufunction(override=True)
    def can_execute(self, context):
        selected_materials = unreal.EditorUtilityLibrary.get_selected_assets_of_class(unreal.MaterialInterface) or []
        return not (selected_materials and self.material in selected_materials)


def setup_menus():
    """Initialize the Master Material System menus"""
    remove_menus()
    material_asset_menu = unreal.ToolMenus.get().extend_menu("ContentBrowser.AssetContextMenu.Material")
    material_instance_asset_menu = unreal.ToolMenus.get().extend_menu(
        "ContentBrowser.AssetContextMenu.MaterialInstanceConstant"
    )
    create_new_asset_menu = unreal.ToolMenus.get().extend_menu("ContentBrowser.AddNewContextMenu")

    material_menus = [
        material_asset_menu,
        material_instance_asset_menu
    ]

    section = "Master Materials"
    for menu_object in material_menus:
        menu_object.add_section(section, section)
    create_new_asset_menu.add_section(section, section)

    # mark as master materials
    ToggleMasterMaterial(material_asset_menu, section)
    
    master_materials = assets.find_assets(metadata={constants.META_IS_MASTER_MATERIAL: True}, class_types=["Material"])

    # Add the drop-down menus to apply/create material instances
    if master_materials:
        master_materials = sorted(
            master_materials,
            key=lambda asset_data: assets.get_metadata(asset_data.get_asset(), constants.META_MATERIAL_DISPLAY_NAME).lower()
        )
        dropdown_menus = list()
        for menu_object in material_menus:
            dropdown_menus.append(
                menu_object.add_sub_menu(
                    MENU_OWNER, section, "ApplyMasterMaterials", "Apply Master Material"
                )
            )
        dropdown_menus.append(
            create_new_asset_menu.add_sub_menu(
                MENU_OWNER, section, "NewFromMasterMaterials", "New From Master Material"
            )
        )

        # Register each master materials to the drop-down menus
        for material_asset_data in master_materials:
            for menu_object in dropdown_menus:
                ApplyMasterMaterial(material_asset_data.get_asset(), menu_object)


def remove_menus():
    unreal.ToolMenus.get().unregister_owner_by_name(MENU_OWNER)
