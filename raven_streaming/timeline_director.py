"""
MiniMax H3 RAVEN Timeline Director Node
---------------------------------------
Universal ingestion engine for multi-shot scripts, JSON chain plans, and screenplay packages.
Supports every standard MiniMax H3 prompt section and setting:
1. subject_definitions: Token declarations binding to reference portraits (@char1, @char2)
2. summary: High-level narrative summary
3. retention_analysis: Persistence flags for character identities and settings
4. detailed_description: 3-Act chronological sub-beats ([0.00s-3.13s] Act I, Act II, Act III)
5. camera_movement: Dolly, tracking, steadycam, crane, aerial, or handheld optics
6. lighting_and_atmosphere: Volumetric backlight, tungsten glow, anamorphic lens flares
7. overall_soundscape: 3D spatial room acoustics (RT60 decay), sub-bass rumble, foley
8. non_diegetic_music: Musical soundtrack cues or score progression
9. CRITICAL RULES: Directives for phoneme lip-sync, texture retention, continuous consistency
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from raven_streaming.scene_vault import SCENE_VAULT


@dataclass
class H3ParsedSections:
    subject_definitions: str = ""
    summary: str = ""
    retention_analysis: str = ""
    detailed_description: str = ""
    camera_movement: str = ""
    lighting_and_atmosphere: str = ""
    overall_soundscape: str = ""
    non_diegetic_music: str = ""
    critical_rules: str = ""
    custom_sections: Dict[str, str] = field(default_factory=dict)


@dataclass
class TimelineShot:
    shot_index: int
    start_seconds: float
    end_seconds: float
    raw_prompt: str
    clean_description: str
    sections: H3ParsedSections = field(default_factory=H3ParsedSections)
    scene_tag: str = "default_scene"


def extract_h3_sections(text: str) -> H3ParsedSections:
    """Extracts all standard MiniMax H3 labeled prompt sections from a text block."""
    sections = H3ParsedSections()
    
    # Section regex patterns
    sec_names = [
        "subject_definitions",
        "summary",
        "retention_analysis",
        "detailed_description",
        "camera_movement",
        "lighting_and_atmosphere",
        "overall_soundscape",
        "non_diegetic_music",
        "CRITICAL RULES"
    ]
    
    pattern = r"(?:^|\n)(subject_definitions|summary|retention_analysis|detailed_description|camera_movement|lighting_and_atmosphere|overall_soundscape|non_diegetic_music|CRITICAL RULES):\s*(.*?)(?=(?:\n(?:subject_definitions|summary|retention_analysis|detailed_description|camera_movement|lighting_and_atmosphere|overall_soundscape|non_diegetic_music|CRITICAL RULES):)|\Z)"
    
    matches = re.findall(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    found_keys = set()
    for key, content in matches:
        k_clean = key.strip().lower().replace(" ", "_")
        c_clean = content.strip()
        found_keys.add(k_clean)
        
        if k_clean == "subject_definitions":
            sections.subject_definitions = c_clean
        elif k_clean == "summary":
            sections.summary = c_clean
        elif k_clean == "retention_analysis":
            sections.retention_analysis = c_clean
        elif k_clean == "detailed_description":
            sections.detailed_description = c_clean
        elif k_clean == "camera_movement":
            sections.camera_movement = c_clean
        elif k_clean == "lighting_and_atmosphere":
            sections.lighting_and_atmosphere = c_clean
        elif k_clean == "overall_soundscape":
            sections.overall_soundscape = c_clean
        elif k_clean == "non_diegetic_music":
            sections.non_diegetic_music = c_clean
        elif k_clean in ("critical_rules", "rules"):
            sections.critical_rules = c_clean
        else:
            sections.custom_sections[k_clean] = c_clean

    # If no detailed_description section explicitly labeled, use remaining raw text
    if not sections.detailed_description and not found_keys:
        sections.detailed_description = text.strip()

    return sections


def compile_h3_prompt(sections: H3ParsedSections, include_rules: bool = True) -> str:
    """Compiles all populated H3 sections back into the official MiniMax format."""
    blocks = []
    
    if sections.subject_definitions:
        blocks.append(f"subject_definitions: {sections.subject_definitions}")
    if sections.summary:
        blocks.append(f"summary: {sections.summary}")
    if sections.retention_analysis:
        blocks.append(f"retention_analysis: {sections.retention_analysis}")
    if sections.detailed_description:
        blocks.append(f"detailed_description: {sections.detailed_description}")
    if sections.camera_movement:
        blocks.append(f"camera_movement: {sections.camera_movement}")
    if sections.lighting_and_atmosphere:
        blocks.append(f"lighting_and_atmosphere: {sections.lighting_and_atmosphere}")
    if sections.overall_soundscape:
        blocks.append(f"overall_soundscape: {sections.overall_soundscape}")
    if sections.non_diegetic_music:
        blocks.append(f"non_diegetic_music: {sections.non_diegetic_music}")
    for k, v in sections.custom_sections.items():
        blocks.append(f"{k}: {v}")
    if include_rules and sections.critical_rules:
        blocks.append(f"CRITICAL RULES:\n{sections.critical_rules}")
        
    return "\n\n".join(blocks)


def parse_timeline_script(script_text: str) -> Tuple[List[TimelineShot], H3ParsedSections]:
    """
    Parses prompt text, JSON chain plans, or screenplay files into structured shots and sections.
    """
    clean_input = script_text.strip()
    global_sections = extract_h3_sections(clean_input)

    # 1. Check if input is a local file path
    if (clean_input.startswith("/") or clean_input.startswith("\\") or (len(clean_input) > 2 and clean_input[1] == ":")) and os.path.exists(clean_input):
        try:
            p = Path(clean_input)
            if p.suffix.lower() == ".json":
                clean_input = p.read_text(encoding="utf-8", errors="ignore")
            elif p.is_dir():
                plan_file = p / "comfyui_chain_plan.json"
                if plan_file.exists():
                    clean_input = plan_file.read_text(encoding="utf-8", errors="ignore")
                else:
                    scene_files = sorted(p.glob("scene_*.txt"))
                    if scene_files:
                        clean_input = "\n\n".join([f"[Shot {i+1}] {sf.read_text(encoding='utf-8', errors='ignore')}" for i, sf in enumerate(scene_files)])
            else:
                clean_input = p.read_text(encoding="utf-8", errors="ignore")
            global_sections = extract_h3_sections(clean_input)
        except Exception as e:
            print(f"[TimelineDirector] Warning reading path {clean_input}: {e}")

    # 2. Check if input is JSON (comfyui_chain_plan.json or standard shots dict)
    if clean_input.startswith("{") and ("\"shots\"" in clean_input or "\"scenes\"" in clean_input):
        try:
            plan_obj = json.loads(clean_input)
            raw_shots = plan_obj.get("shots", []) or plan_obj.get("scenes", [])
            shots = []
            for i, s in enumerate(raw_shots, 1):
                p_text = s.get("prompt", "")
                dur = float(s.get("duration_seconds", 3.0))
                start_sec = (i - 1) * dur
                shot_secs = extract_h3_sections(p_text)
                
                # Inherit global soundscape/subject_definitions if not defined per shot
                if not shot_secs.subject_definitions and global_sections.subject_definitions:
                    shot_secs.subject_definitions = global_sections.subject_definitions
                if not shot_secs.overall_soundscape and global_sections.overall_soundscape:
                    shot_secs.overall_soundscape = global_sections.overall_soundscape

                shots.append(TimelineShot(
                    shot_index=i,
                    start_seconds=start_sec,
                    end_seconds=start_sec + dur,
                    raw_prompt=p_text,
                    clean_description=p_text,
                    sections=shot_secs,
                    scene_tag=s.get("title", f"shot_{i}")
                ))
            return shots, global_sections
        except Exception as e:
            print(f"[TimelineDirector] JSON parse warning: {e}, falling back to text parsing.")

    # 3. Parse [Shot N] blocks
    shot_blocks = re.findall(
        r"\[(?:Shot|shot)\s*(\d+)\]\s*(?:At\s*(\d{2}:\d{2}(?:\.\d{3})?))?,?\s*(.*?)(?=\[(?:Shot|shot)|\Z|overall_soundscape:|non_diegetic_music:|CRITICAL RULES:)",
        clean_input,
        flags=re.DOTALL | re.IGNORECASE
    )

    shots = []
    for idx_str, time_str, content in shot_blocks:
        shot_idx = int(idx_str) if idx_str else len(shots) + 1
        start_sec = 0.0
        if time_str:
            parts = time_str.split(":")
            if len(parts) == 2:
                start_sec = float(parts[0]) * 60.0 + float(parts[1])
        else:
            start_sec = len(shots) * 3.0

        clean_text = content.strip()
        shot_secs = extract_h3_sections(clean_text)
        
        # Inherit global sections
        if not shot_secs.subject_definitions and global_sections.subject_definitions:
            shot_secs.subject_definitions = global_sections.subject_definitions
        if not shot_secs.overall_soundscape and global_sections.overall_soundscape:
            shot_secs.overall_soundscape = global_sections.overall_soundscape
        if not shot_secs.critical_rules and global_sections.critical_rules:
            shot_secs.critical_rules = global_sections.critical_rules

        shots.append(TimelineShot(
            shot_index=shot_idx,
            start_seconds=start_sec,
            end_seconds=start_sec + 3.0,
            raw_prompt=clean_text,
            clean_description=clean_text,
            sections=shot_secs
        ))

    # Calculate end timestamps
    for i in range(len(shots) - 1):
        shots[i].end_seconds = shots[i + 1].start_seconds

    if not shots:
        # Fallback: treat entire string as Shot 1
        shots.append(TimelineShot(
            shot_index=1,
            start_seconds=0.0,
            end_seconds=10.0,
            raw_prompt=clean_input,
            clean_description=clean_input,
            sections=global_sections
        ))

    return shots, global_sections


class RavenTimelineDirectorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "script_timeline": ("STRING", {
                    "multiline": True,
                    "default": (
                        "subject_definitions: <LEAD_A> is the focal protagonist in cinematic attire visible in @char1 and <LEAD_B> is the secondary lead visible in @char2.\n\n"
                        "summary: [reference generation] The target sequence captures an intense dramatic exchange between two leads.\n\n"
                        "retention_analysis: <LEAD_A> (present throughout): fully_preserved. <LEAD_B> (present throughout): fully_preserved.\n\n"
                        "[Shot 1] At 00:00.000, detailed_description: [0.00s-3.13s] Act I (Spatial Framing & Atmosphere): Camera opens on an intimate establishing medium shot with volumetric tungsten rim lighting catching ambient atmospheric dust...\n\n"
                        "[Shot 2] At 00:03.000, detailed_description: [3.13s-6.27s] Act II (Physical Choreography & Quoted Dialogue): Smooth tracking push-in as <LEAD_A> steps closer with intense micro-acting focus, saying: \"Are you sure about this?\" with visible phoneme lip-sync...\n\n"
                        "camera_movement: Slow steadycam push-in transitioning to a gentle orbital arc, 35mm anamorphic prime lens at T1.5 with shallow depth of field.\n\n"
                        "lighting_and_atmosphere: High-contrast chiaroscuro lighting, deep shadow rolloff, natural cinematic lens flare.\n\n"
                        "overall_soundscape: Intimate interior room tone RT60=0.35s, soft fabric rustle, warm low-frequency 45Hz sub-bass presence, crisp clear dialogue without muffling.\n\n"
                        "non_diegetic_music: N/A\n\n"
                        "CRITICAL RULES:\n"
                        "- Consistent facial identity and wardrobe throughout.\n"
                        "- Precise visible lip-sync phoneme articulation and natural jaw cadence."
                    )
                }),
                "shot_mode": ([
                    "Continuous_Sequence (All Shots Combined)",
                    "Shot 1 (Initial Beat)",
                    "Shot 2",
                    "Shot 3",
                    "Shot 4",
                    "Shot 5",
                    "Shot 6",
                    "Shot 7",
                    "Shot 8"
                ],),
                "auto_save_scenes_to_vault": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "plan_json_input": ("STRING", {"multiline": True, "default": ""}),
                "active_scene_id": ("STRING", {"default": "scene_01"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = (
        "active_prompt",
        "subject_definitions",
        "overall_soundscape",
        "detailed_description",
        "total_shots",
        "timeline_summary"
    )
    FUNCTION = "direct_timeline"
    CATEGORY = "MiniMax_H3/Director"

    def direct_timeline(
        self,
        script_timeline: str,
        shot_mode: str = "Continuous_Sequence (All Shots Combined)",
        auto_save_scenes_to_vault: bool = True,
        plan_json_input: str = "",
        active_scene_id: str = "scene_01"
    ) -> Tuple[str, str, str, str, int, str]:
        
        # Priority: if plan_json_input is provided and non-empty, use it
        source_text = plan_json_input.strip() if plan_json_input and len(plan_json_input.strip()) > 5 else script_timeline

        shots, global_sections = parse_timeline_script(source_text)

        # Build prompt based on mode
        if "Continuous_Sequence" in shot_mode:
            # Combine header + all shots + soundscape + rules
            compiled_parts = []
            
            # 1. Subject definitions
            if global_sections.subject_definitions:
                compiled_parts.append(f"subject_definitions: {global_sections.subject_definitions}")
            if global_sections.summary:
                compiled_parts.append(f"summary: {global_sections.summary}")
            if global_sections.retention_analysis:
                compiled_parts.append(f"retention_analysis: {global_sections.retention_analysis}")

            # 2. Sequential shots
            for s in shots:
                compiled_parts.append(f"[Shot {s.shot_index}] {s.clean_description}")

            # 3. Environment & Acoustics
            if global_sections.camera_movement:
                compiled_parts.append(f"camera_movement: {global_sections.camera_movement}")
            if global_sections.lighting_and_atmosphere:
                compiled_parts.append(f"lighting_and_atmosphere: {global_sections.lighting_and_atmosphere}")
            if global_sections.overall_soundscape:
                compiled_parts.append(f"overall_soundscape: {global_sections.overall_soundscape}")
            if global_sections.non_diegetic_music:
                compiled_parts.append(f"non_diegetic_music: {global_sections.non_diegetic_music}")
            if global_sections.critical_rules:
                compiled_parts.append(f"CRITICAL RULES:\n{global_sections.critical_rules}")

            active_prompt = "\n\n".join(compiled_parts)
            active_desc = "\n\n".join([f"[Shot {s.shot_index}] {s.clean_description}" for s in shots])
            mode_desc = f"Continuous master stream ({len(shots)} shots combined)"
        else:
            # Select specific shot index (e.g. "Shot 2" -> 2)
            shot_num = 1
            m = re.search(r"Shot\s*(\d+)", shot_mode)
            if m:
                shot_num = int(m.group(1))

            target_shot = next((s for s in shots if s.shot_index == shot_num), shots[0] if shots else None)
            if target_shot:
                # Compile complete prompt for this single shot
                compiled_shot = compile_h3_prompt(target_shot.sections, include_rules=True)
                active_prompt = compiled_shot if compiled_shot else target_shot.clean_description
                active_desc = target_shot.sections.detailed_description or target_shot.clean_description
                mode_desc = f"Single shot beat: Shot {target_shot.shot_index}"
            else:
                active_prompt = source_text
                active_desc = source_text
                mode_desc = "Fallback prompt"

        subj = global_sections.subject_definitions
        sound = global_sections.overall_soundscape or "Cinematic ambient soundscape."
        summary = f"Scene '{active_scene_id}': {len(shots)} total shots parsed. Mode: {mode_desc}."
        
        print(f"[TimelineDirector] {summary}")
        return (active_prompt, subj, sound, active_desc, len(shots), summary)


NODE_CLASS_MAPPINGS = {
    "RavenTimelineDirector": RavenTimelineDirectorNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RavenTimelineDirector": "RAVEN Timeline Director & Multi-Shot Stepper"
}
