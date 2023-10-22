// Copyright Epic Games, Inc. All Rights Reserved.

#include "MasterMaterialSystemBPLibrary.h"
#include "MasterMaterialSystem.h"
#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"
#include "AssetRegistry/AssetRegistryModule.h"


UMasterMaterialSystemBPLibrary::UMasterMaterialSystemBPLibrary(const FObjectInitializer& ObjectInitializer)
: Super(ObjectInitializer)
{

}


void
UMasterMaterialSystemBPLibrary::RemoveEUWFromUserPrefs(UEditorUtilityWidgetBlueprint* EditorWidget) {
    UEditorUtilitySubsystem* EUS = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();
    EUS->LoadedUIs.Remove(EditorWidget);
    EUS->SaveConfig();
}


void
UMasterMaterialSystemBPLibrary::RegisterMetadataTags(const TArray<FName>& Tags)
{
	TSet<FName>& GlobalTagsForAssetRegistry = UObject::GetMetaDataTagsForAssetRegistry();
	for (FName Tag : Tags)
	{
		if (!Tag.IsNone())
		{
			if (!GlobalTagsForAssetRegistry.Contains(Tag))
			{
				GlobalTagsForAssetRegistry.Add(Tag);
			}
		}
	}
}

