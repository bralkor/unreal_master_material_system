// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "EditorUtilityWidgetBlueprint.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MasterMaterialSystemBPLibrary.generated.h"

/*
*/
UCLASS()
class UMasterMaterialSystemBPLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_UCLASS_BODY()


    /**  Remove the given Editor Utility Widget from the User Prefs
     * @param  EditorWidget  the Editor Tool Instance
     */
    UFUNCTION(BlueprintCallable, Category = "Master Materials", meta = (DefaultToSelf="EditorWidget"))
    static void RemoveEUWFromUserPrefs(UEditorUtilityWidgetBlueprint* EditorWidget);


    /**  Add the given metadata tag names to the Asset Registry
     * @param  Redirectors  the redirectors to fix
     */
    UFUNCTION(BlueprintCallable, Category = "Master Materials")
    static void RegisterMetadataTags(const TArray<FName>& Tags);

};
