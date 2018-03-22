# --- UCSF Chimera Copyright ---
# Copyright (c) 2000 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  This notice must be embedded in or
# attached to all copies, including partial copies, of the
# software or any revisions or derivations thereof.
# --- UCSF Chimera Copyright ---

import chimera.extension

class OrbiTrajEMO(chimera.extension.EMO):
    def name(self):
        return 'Tangram OrbiTraj'
    def description(self):
        return 'Playback of Orbital trajectories'
    def categories(self):
        return ['InsiliChem']
    def icon(self):
        return
    def activate(self):
	# Call the 'Movie' function in the "__init__.py" module.
        self.module().launch()
	return None

chimera.extension.manager.registerExtension(OrbiTrajEMO(__file__))
