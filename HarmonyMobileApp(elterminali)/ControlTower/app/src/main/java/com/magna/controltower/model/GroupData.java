package com.magna.controltower.model;

public class GroupData {
    private final String name;
    private final String status;

    public GroupData(String name, String status) {
        this.name = name;
        this.status = status;
    }
    public String getName() { return name; }
    public String getStatus() { return status; }
}
