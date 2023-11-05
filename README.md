<br></br>

<h1 align="center">Unreal Master Material System</h1>

<p align="center">
A Master Material System plugin for UE5<br>
created by <a href="https://www.linkedin.com/in/bkortbus/">Brian Kortbus</a>
<br>
<br>
<a href="https://youtu.be/5u_jgtToYwE">Youtube Demo Video</a>

</p>
<br>


## Overview
<ul>

Master Materials are parent materials we wish to make Material Instances of to use on our assets in Unreal. 
Using Material Instances can greatly improve material performance and can streamline the customization
of common materials for all of our unique assets. To learn more about Material Instances, 
[the Epic docs provide a good overview of Material Instances](
https://docs.unrealengine.com/5.3/en-US/instanced-materials-in-unreal-engine/
).

This plugin adds a Master Material system to the Content Browser's right click menu. Materials may be
registered or unregistered as Master Materials in this system. With a Master Material registered, this
toolset adds a right click menu option to create new Material Instances in any Content Browser folder.

With another material selected, we can also apply a Master Material to that material. This provides an
editor tool window in which we may transfer textures to the new Material Instance's parameter slots. 
This window also provides an option to update any Static or Skeletal Meshes to use this new Material
Instance.

</ul><br><br>



## Registering a Master Material

<ul>

The first step is to register a material as a Master Material in the right click menu:

<img src="resources/MM_mark_material.gif" width="600">

In the Content Browser, with a Material selected, use the new `Register Master Material` option
found in the Right Click Menu under the `Master Material` section.

A popup window will let us set the Master Material's display name in the system:

<ul>
<img src="resources/MM_display_name.png" width="300">
</ul>

Once the display name is chosen, our new Master Material will be listed in the `Apply Master Material` 
dropdown menu:

<ul>
<img src="resources/MM_registered_material.png" width="400">
</ul>

</ul><br><br>



## Create from Master Material as is

<ul>

The most direct feature is to create a new Material Instance from a Master Material in the current Content Browser folder
as is. With nothing selected in the Content Browser, the right click dropdown menu will display as `New From Master Material`:

<ul>
<img src="resources/MM_create_MI_as_is.png" width="450">
</ul>

This will quickly create a new MI in the current Content Browser folder that we can then rename/edit:

<ul>
<img src="resources/MM_new_MI.png" width="250">
</ul>

</ul><br><br>



## Applying a Master Material

<ul>

A more interactive feature is the ability to apply a Master Material to another material. This gives us the option
to transfer textures over to the new Material Instance and the option to update any assets using the old material to
use the newly created Material Instance:

<img src="resources/MM_apply_master_material.gif" width="600">

Applying a Master Material will create a new Material Instance of the desired Master Material next
to the selected material in the Content Browser that we want to replace.

A tool window will let us transfer any textures over to this new Material Instance's texture parameters
from the old material:

<ul>
<img src="resources/MM_gui.png" width="350">
</ul>

Each Texture Parameter will have a slot in the UI. Use the dropdown menu for each texture parameter slot
to transfer a texture from the material we're replacing. The texture marked with `(default)` is the Master
Material's default parameter value, all other textures in the dropdown menu are sourced from the old material.

<br>

If `Replace Mesh References` is checked, any Static Meshes or Skeletal Meshes using the old material will
be updated to use the new Material Instance.

<br>

From the Gif Example above, I updated the new instance's `Normal` and `Texture` parameters with textures from
the wolf's original material:

<ul>
<img src="resources/MM_new_instance_textures.png" width="600">
</ul>

<br>

The new material instance next to the one it replaced:

<ul>
<img src="resources/MM_new_material.png" width="350">
</ul>

</ul><br><br>



## Applying over a Material Instance

<ul>

We can also apply a Master Material to a Material Instance as well! Using the results
of the previous section, here is the window if we apply a Master Material to that Material Instance:

<ul>
<img src="resources/MM_applying_on_a_MI.png" width="350">
</ul>

When transferring textures from a Material Instance it will use the parameter names instead of the texture names.
In this case we are transferring from the old material's parameter slots to the new material's parameter slots,
focusing on the use of the texture rather than its file name.

</ul><br><br>



## Unregistering a Master Material

<ul>

To remove a Master Material from the system, right-click on the material asset and select
the `Unregister` option:

<ul>
<img src="resources/MM_unregister.png" width="350">
</ul>

This will not delete the material or change any existing assets beyond removing it from the list
of available Master Materials.

</ul><br><br>



## Update Log

<ul>

4 November 2023

<ul>

- updated README
- fixed tooltip typo
</ul>


</ul><br><br>
