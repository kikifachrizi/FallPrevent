#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>
#include <std_msgs/msg/string.hpp>

#include <deque>
#include <vector>
#include <fstream>
#include <filesystem>

using std::placeholders::_1;

class DataProcessingNode : public rclcpp::Node
{
public:
    DataProcessingNode() : Node("data_processing_node")
    {
        sub_depth_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
            "/depth_frame", 10,
            std::bind(&DataProcessingNode::depthCallback, this, _1));

        sub_label_ = this->create_subscription<std_msgs::msg::String>(
            "/activity_label", 10,
            std::bind(&DataProcessingNode::labelCallback, this, _1));

        // 🔥 UPDATED PARAMETER
        sequence_length_ = 90;   // lebih panjang (capture full fall)
        stride_ = 45;            // 50% overlap

        dataset_path_ = std::string(std::getenv("HOME")) + "/dataset/";
        std::filesystem::create_directories(dataset_path_);

        RCLCPP_INFO(this->get_logger(), "Data Processing Node Ready");
    }

private:
    rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr sub_depth_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_label_;

    std::deque<std::vector<float>> buffer_;

    std::string current_label_ = "none";
    std::string sequence_label_ = "none";

    bool is_recording_ = false;

    int sequence_length_;
    int stride_;
    int seq_counter_ = 0;

    std::string dataset_path_;

    // ===== LABEL CALLBACK =====
    void labelCallback(const std_msgs::msg::String::SharedPtr msg)
    {
        std::string cmd = msg->data;

        // 🔥 CONTROL RECORDING
        if (cmd == "start_fall" || cmd == "start_walk")
        {
            is_recording_ = true;
            buffer_.clear();

            current_label_ = (cmd == "start_fall") ? "fall" : "non_fall";

            std::filesystem::create_directories(dataset_path_ + current_label_);

            RCLCPP_INFO(this->get_logger(), "START RECORDING: %s", current_label_.c_str());
        }
        else if (cmd == "stop")
        {
            is_recording_ = false;
            buffer_.clear();

            RCLCPP_INFO(this->get_logger(), "STOP RECORDING");
        }
    }

    // ===== DEPTH CALLBACK =====
    void depthCallback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
    {
        if (!is_recording_)
            return;

        std::vector<float> frame = msg->data;

        // 🔥 SNAPSHOT LABEL SAAT SEQUENCE DIMULAI
        if (buffer_.empty())
        {
            sequence_label_ = current_label_;
        }

        buffer_.push_back(frame);

        if (buffer_.size() >= sequence_length_)
        {
            saveSequence();

            // sliding window
            for (int i = 0; i < stride_; i++)
                buffer_.pop_front();
        }
    }

    // ===== SAVE FUNCTION =====
    void saveSequence()
    {
        std::string folder = dataset_path_ + sequence_label_;

        std::string filename = folder + "/seq_" + std::to_string(seq_counter_++) + ".bin";

        std::ofstream file(filename, std::ios::binary);

        for (auto &frame : buffer_)
        {
            file.write(reinterpret_cast<char*>(frame.data()),
                       frame.size() * sizeof(float));
        }

        file.close();

        RCLCPP_INFO(this->get_logger(), "Saved: %s", filename.c_str());
    }
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<DataProcessingNode>());
    rclcpp::shutdown();
    return 0;
}