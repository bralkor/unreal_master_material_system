from master_materials import (
    bplibrary,
    constants,
    menus
)

import unreal


# register metadata names
unreal.MasterMaterialSystemBPLibrary.register_metadata_tags([
    constants.META_MATERIAL_DISPLAY_NAME,
    constants.META_IS_MASTER_MATERIAL
])

# register the menu system
menus.setup_menus()
