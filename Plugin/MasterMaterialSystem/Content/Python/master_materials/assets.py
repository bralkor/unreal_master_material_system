
from master_materials import constants

from master_materials.unreal_systems import (
    asset_registry,
    asset_registry_helper,
    EditorActorSubsystem,
    EditorAssetLibrary,
    EditorAssetSubsystem
)

import unreal


def set_metadata(asset, key, value):
    """
    Setting Metadata is done on a loaded unreal.Object reference

    parameters:
        asset: the asset to save the metadata to
        key:   the metadata key name
        value: the metadata value
    """
    EditorAssetLibrary.set_metadata_tag(asset, key, str(value))


def get_metadata(asset, key, default=None):
    """
    Getting Metadata can be done on a loaded unreal.Object reference OR unreal.AssetData

    using METADATA_TYPE_MAP we can automatically convert
    our metadata into their intended types (if not string)

    parameters:
        asset: the asset to get the metadata from
        key:   the metadata key name
        default: the default value to assume if the metadata is not set

    Return:
        the metadata value in its expected type (if mapped in METADATA_TYPE_MAP)
    """
    # Get the metadata value from the loaded asset or an AssetData instance
    if isinstance(asset, unreal.AssetData):
        value = asset.get_tag_value(key)
    else:
        value = EditorAssetLibrary.get_metadata_tag(asset, key)

    if value and value.lower != "none":
        # Get this metadata key's expected value type:
        value_type = constants.METADATA_TYPE_MAP.get(key, str)

        if value_type == bool:
            # bools are a special case as bool(str) only checks for length
            return value.lower() == "true"
        else:
            # most value types may be directly converted
            return value_type(value)

    return default


def find_assets(name="", str_in_path="", exact_match=False, metadata=None, class_types=None):
    """Find Unreal Assets based on a given name, a list of class names, or metadata {name:value} pairs

    parameters:
        name (str): the asset name to search for
        str_in_path (str): look for assets based on a substring of the package path
        exact_match (bool): If true, only return exact name matches. False will test as 'A in B' 
        metadata (dict): a dictionary of metadata name:value pairs
        class_type (list(str)): list of Unreal class type (Object, LevelSequence, Level, etc)

    returns:
        list(unreal.AssetData):
    """
    metadata = metadata or {}
    class_types = class_types or ["object"]

    # Create basic filter for the given class types and perform an initial search
    base_filter = unreal.ARFilter(
        class_names=class_types,
        recursive_paths=True,
    )
    results = asset_registry.get_assets(base_filter) or []

    # Remove any Temp asset paths
    results = [r for r in results if not str(r.package_path).startswith("/Temp/")]

    # Filter results by each metadata key:value pair
    for key, value in metadata.items():
        query = unreal.TagAndValue(key, str(value))
        meta_filter = asset_registry_helper.set_filter_tags_and_values(base_filter, [query])
        results = asset_registry.run_assets_through_filter(results, meta_filter) or []
        if not results:
            break

    # Filter results by name (if provided)
    if name:
        # use exact match (a==b) or partial (a in b)
        name_matches_filter = (
            lambda a, b: a == b if exact_match else a.lower() in b.lower()
        )
        results = [r for r in results if name_matches_filter(name, str(r.asset_name))]

    # Filter results by package path (if provided)
    if str_in_path:
        results = [r for r in results if str_in_path.lower() in str(r.package_name).lower()]

    # Sort results by asset path, list local assets before any plugin assets
    if len(results) > 1:
        results = sorted(
            results,
            key=lambda p: (
                not str(p.package_path).startswith("/Game/"),  # False is 0 True is 1
                str(p.package_path)
            )
        )

    return list(results)


def get_all_actors():
    """
    Get all actors including Sequencer spawned actors

    return:
        list(unreal.Actor): list of all actors in the currently open level
    """
    scene_components = EditorActorSubsystem.get_all_level_actors_components()
    return sorted(
        list({
            i.get_owner()
            for i in scene_components
            if i.get_owner()
            and unreal.MathLibrary.class_is_child_of(i.get_owner().get_class(), unreal.Actor)
        }),
        key=lambda a: a.get_path_name()
    )


def save_asset(asset):
    """Save the given asset or asset path

    parameters:
        asset (str or unreal.Object): the asset to save

    return:
        bool: if the operation was a success
    """
    if isinstance(asset, unreal.Package):
        return unreal.EditorLoadingAndSavingUtils.save_packages([asset], False)

    asset_path = asset if isinstance(asset, str) else asset.get_outermost().get_path_name()
    return EditorAssetSubsystem.save_asset(asset_path)
