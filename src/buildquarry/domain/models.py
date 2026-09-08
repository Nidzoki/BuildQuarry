"""Validated domain models shared by planner and UI."""

from typing import Literal

from pydantic import BaseModel, Field

TimeBudget = Literal["weekend", "one_week", "two_weeks", "one_month"]


class ProjectInput(BaseModel):
    idea: str = Field(min_length=10)
    target_user: str = Field(min_length=2)
    time_budget: TimeBudget
    skill_level: str = Field(min_length=2)
    tech_stack: str = ""
    constraints: str = ""


class Milestone(BaseModel):
    title: str
    tasks: list[str] = Field(min_length=1)


class Plan(BaseModel):
    title: str
    mvp: str
    primary_user: str
    in_scope: list[str] = Field(min_length=1)
    out_of_scope: list[str] = Field(min_length=1)
    milestones: list[Milestone] = Field(min_length=1)
    acceptance_criteria: list[str] = Field(min_length=1)
    architecture: list[str] = Field(default_factory=list)
    data_model: list[str] = Field(default_factory=list)
    api_design: list[str] = Field(default_factory=list)
    technical_risks: list[str] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)
