package com.magna.controltower.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.magna.controltower.R;
import com.magna.controltower.model.GroupData;
import java.util.List;

public class GroupAdapter extends RecyclerView.Adapter<GroupAdapter.VH> {

    public interface OnGroupClick { void onClick(GroupData group); }

    private final List<GroupData> items;
    private final OnGroupClick listener;

    public GroupAdapter(List<GroupData> items, OnGroupClick listener) {
        this.items = items;
        this.listener = listener;
    }

    @NonNull @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_group_button, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH h, int position) {
        GroupData g = items.get(position);
        h.tvGroupName.setText(g.getName());
        h.tvStatus.setText(g.getStatus());

        // Tıklama
        h.itemRoot.setOnClickListener(v -> {
            if (listener != null) listener.onClick(g);
        });
    }

    @Override public int getItemCount() { return items.size(); }

    static class VH extends RecyclerView.ViewHolder {
        View itemRoot;
        TextView tvGroupName, tvStatus;
        VH(@NonNull View itemView) {
            super(itemView);
            // id’ler item_group_button.xml ile birebir aynı olmalı
            itemRoot   = itemView.findViewById(R.id.itemRoot);
            tvGroupName = itemView.findViewById(R.id.tvGroupName);
            tvStatus = itemView.findViewById(R.id.statusPill);

            // itemRoot yoksa, kökü kullan:
            if (itemRoot == null) itemRoot = itemView;
        }
    }
}
